try:
    from fastapi import FastAPI, File, Form, UploadFile, HTTPException
    from fastapi.responses import FileResponse
    import uvicorn
    import numpy as np
    from fastapi.middleware.cors import CORSMiddleware
    import os
    from dotenv import load_dotenv
    import traceback
    
    load_dotenv() 
    
    # === 依赖：假设所有模块都与 main.py 同级 ===
    from feature_extractor import load_models, get_feature_vector, get_tags_from_image
    from sync_utils import pull_data, push_data
    from data_manager import get_all_items, add_item, filter_items, get_item_by_vec_id
    from retrieval_engine import (
        build_or_load_index,
        search_in_index,
        add_to_index,
        save_index
    )
    
    import os
    import uuid
except Exception:
    traceback.print_exc()
    raise

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================
# 全局变量与初始化
# =========================================
IMAGE_DIR = "images"
INDEX_PATH = "vectors.index"
DATABASE_PATH = "database.json"
HUGGING_FACE_TOKEN = os.getenv("HF_TOKEN")

if HUGGING_FACE_TOKEN:
    pull_data(HUGGING_FACE_TOKEN)
else:
    print("警告：未配置 HF_TOKEN，使用本地数据。")

# 加载模型
clip_model, ocr_model = load_models()

if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# 加载索引
items = get_all_items()
if os.path.exists(INDEX_PATH):
    index = build_or_load_index(None, INDEX_PATH)
else:
    index = build_or_load_index(np.zeros((0, 512)).astype("float32"), INDEX_PATH)


# ============================================================
# POST /api/items   上传单个失物
# ============================================================
@app.post("/api/items")
async def upload_item(
    file: UploadFile = File(...),
    description: str = Form(...),
    location: str = Form(...),
    category: str = Form(...),
    contact: str = Form(...),
    item_type: str = Form(...),
):
    try:
        raw_bytes = await file.read()
        filename = f"{uuid.uuid4().hex}.jpg"
        file_path = os.path.join(IMAGE_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(raw_bytes)

        # 特征提取
        vector = get_feature_vector(clip_model, image_bytes=raw_bytes)
        
        # OCR (带容错)
        tags = []
        try:
            baidu_api_key = os.getenv("BAIDU_API_KEY")
            baidu_secret_key = os.getenv("BAIDU_SECRET_KEY")
            tags = get_tags_from_image(ocr_model, raw_bytes, baidu_api_key, baidu_secret_key)
        except Exception as e:
            print(f"标签提取警告: {e}")
            tags = [] # 确保失败也是个空列表

        # 更新索引
        vector_np = np.array([vector], dtype="float32")
        vec_id = index.ntotal
        add_to_index(index, vector_np)
        save_index(index, INDEX_PATH)

        # 更新数据库
        new_item = add_item(
            vec_id=vec_id,
            description=description,
            location=location,
            category=category,
            image_filename=filename,
            tags=tags,
            contact=contact,
            item_type=item_type
        )

        # 同步云端
        if HUGGING_FACE_TOKEN:
            try:
                push_data(HUGGING_FACE_TOKEN, file_path)
                push_data(HUGGING_FACE_TOKEN, DATABASE_PATH)
                push_data(HUGGING_FACE_TOKEN, INDEX_PATH)
            except Exception as e:
                print(f"云端同步失败: {e}")

        return {"status": "success", "item": new_item}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# POST /api/search   混合检索 (修复版 - 防崩溃)
# ============================================================
@app.post("/api/search")
async def search_items(
    query_text: str = Form(None),
    query_image: UploadFile = File(None),
    location: str = Form(None),
    category: str = Form(None),
    date_range_start: str = Form(None),
    date_range_end: str = Form(None),
):
    try:
        # Step 1：过滤
        candidates = filter_items(
            location=location,
            category=category,
            date_range_start=date_range_start,
            date_range_end=date_range_end
        )

        if len(candidates) == 0:
            return {"results": []}

        # Step 2：查询向量
        if query_text is None and query_image is None:
            # 如果没有查询条件，直接返回按时间排序的过滤结果
            candidates.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return {"results": candidates}

        if query_image:
            raw = await query_image.read()
            query_vec = get_feature_vector(clip_model, image_bytes=raw)
        else:
            query_vec = get_feature_vector(clip_model, text=query_text)

        query_vec_np = np.array([query_vec]).astype("float32")

        # Step 3：语义检索
        top_k = min(100, len(candidates)) # Top-K 100
        if top_k <= 0 or index.ntotal == 0:
            return {"results": []}
            
        distances, ids = search_in_index(index, query_vec_np, top_k)
        
        # [安全修复] 语义分数表
        semantic_scores_raw = {}
        if len(ids) > 0:
            for dist, vid in zip(distances[0], ids[0]):
                if vid == -1: continue 
                semantic_scores_raw[int(vid)] = 1.0 / (dist + 1e-9)

        # Step 4：关键词匹配 & 归一化准备
        keyword_scores_raw = {}
        query_tokens = []
        if query_text:
            query_tokens = query_text.lower().split()

        for item in candidates:
            # [安全修复] 强制转int，防止类型不匹配
            try:
                vec_id = int(item['vec_id'])
            except:
                continue

            # 如果不在语义召回范围内，跳过 (Top-100 逻辑)
            if vec_id not in semantic_scores_raw:
                continue
            
            # [安全修复] 防止 tags 为 None 导致 join 崩溃
            tags_list = item.get("tags")
            if tags_list is None: 
                tags_list = []
            
            # [安全修复] 防止 description 为 None
            desc_text = item.get("description") or ""
            
            content_to_match = (desc_text + " " + " ".join(tags_list)).lower()
            
            score = 0.0
            if query_tokens:
                score = sum(1.0 for token in query_tokens if token in content_to_match)
            keyword_scores_raw[vec_id] = score

        # Step 5：归一化
        max_semantic = max(semantic_scores_raw.values()) if semantic_scores_raw else 1.0
        max_keyword = max(keyword_scores_raw.values()) if keyword_scores_raw else 1.0
        
        if max_semantic == 0: max_semantic = 1.0
        if max_keyword == 0: max_keyword = 1.0

        # Step 6：加权融合 (Alpha=0.8)
        ALPHA = 0.8 
        results = []
        
        for item in candidates:
            try:
                vec_id = int(item['vec_id'])
            except:
                continue
            
            if vec_id in semantic_scores_raw:
                s_raw = semantic_scores_raw[vec_id]
                k_raw = keyword_scores_raw.get(vec_id, 0.0)
                
                norm_s = s_raw / max_semantic
                norm_k = k_raw / max_keyword
                
                final_score = (ALPHA * norm_s) + ((1 - ALPHA) * norm_k)
                item["score"] = final_score
                results.append(item)

        results.sort(key=lambda x: x["score"], reverse=True)
        return {"results": results}

    except Exception as e:
        # [关键] 捕获所有错误并打印日志，防止 500 导致前端无响应
        print("Search API Error:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/items")
async def get_all_items_endpoint():
    items = get_all_items()
    sorted_items = sorted(items, key=lambda x: x.get('timestamp', ''), reverse=True)
    return {"results": sorted_items}


@app.get("/api/images/{filename}")
async def get_image(filename: str):
    filepath = os.path.join(IMAGE_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, "图片未找到")
    return FileResponse(filepath)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
