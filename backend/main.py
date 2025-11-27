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
    # 这一步是为了把隐藏的错误打印到日志里
    traceback.print_exc()
    raise

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境请改为具体的域名
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

# 从环境变量获取 Hugging Face Token，这是持久化数据的关键
HUGGING_FACE_TOKEN = os.getenv("HF_TOKEN")

# 启动时，先从云端同步数据
if HUGGING_FACE_TOKEN:
    pull_data(HUGGING_FACE_TOKEN)
else:
    print("警告：未配置 HF_TOKEN，无法从云端同步数据。将使用本地数据（如果存在）。")


# 加载 AI 模型
clip_model, ocr_model = load_models()

# 确保图片目录存在
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# 加载或构建向量索引
# 注意：此时 database.json 应该已经是云端同步下来的最新版本
items = get_all_items()
if os.path.exists(INDEX_PATH):
    index = build_or_load_index(None, INDEX_PATH) # 传 None 强制从文件加载
else:
    # 如果云端也没有 index 文件（首次启动），则创建一个空的
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
    contact: str = Form(...),     # <-- 新增
    item_type: str = Form(...),   # <-- 新增 ("found" or "lost")
):
    # -----------------------------
    # 1. 保存图片到本地临时文件系统
    # -----------------------------
    raw_bytes = await file.read()
    filename = f"{uuid.uuid4().hex}.jpg"
    file_path = os.path.join(IMAGE_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(raw_bytes)

    # -----------------------------
    # 2. 提取多模态特征
    # -----------------------------
    try:
        vector = get_feature_vector(
            clip_model=clip_model,
            image_bytes=raw_bytes,
            text=None
        )

        baidu_api_key = os.getenv("BAIDU_API_KEY")
        baidu_secret_key = os.getenv("BAIDU_SECRET_KEY")

        tags = get_tags_from_image(
            ocr_model=ocr_model,
            image_bytes=raw_bytes,
            api_key=baidu_api_key,
            secret_key=baidu_secret_key
        )
    except Exception as e:
        print(f"特征提取失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"特征提取失败: {str(e)}")

    # -----------------------------
    # 3. 更新本地向量索引
    # -----------------------------
    vector_np = np.array([vector], dtype="float32")
    vec_id = index.ntotal
    add_to_index(index, vector_np)
    save_index(index, INDEX_PATH) # 更新本地 vectors.index

    # -----------------------------
    # 4. 更新本地元数据库
    # -----------------------------
    new_item = add_item(
        vec_id=vec_id,
        description=description,
        location=location,
        category=category,
        image_filename=filename,
        tags=tags,
        contact=contact,         # <-- 新增
        item_type=item_type      # <-- 新增
    )

    # -----------------------------
    # 5. [关键] 将所有本地改动推送回云端进行持久化
    # -----------------------------
    if not HUGGING_FACE_TOKEN:
        print("警告：未在 Space Secrets 中找到 HF_TOKEN，本次上传无法被永久保存！")
    else:
        try:
            print("开始将文件同步到 Hugging Face Dataset...")
            push_data(HUGGING_FACE_TOKEN, file_path)
            push_data(HUGGING_FACE_TOKEN, DATABASE_PATH)
            push_data(HUGGING_FACE_TOKEN, INDEX_PATH)
            print("文件同步成功！")
        except Exception as e:
            print(f"严重错误：数据持久化到 Hugging Face Dataset 失败: {e}")
            # 生产环境中可能需要回滚本地更改或加入重试队列
            raise HTTPException(status_code=500, detail=f"数据保存至云端失败: {e}")

    return {
        "status": "success",
        "item": new_item
    }


# ============================================================
# POST /api/search   混合检索
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
    # Step 1：先进行元数据过滤
    candidates = filter_items(
        location=location,
        category=category,
        date_range_start=date_range_start,
        date_range_end=date_range_end
    )

    if len(candidates) == 0:
        return {"results": []}

    # Step 2：生成查询向量
    if query_text is None and query_image is None:
        raise HTTPException(400, "query_text 和 query_image 至少提供一个")

    if query_image:
        raw = await query_image.read()
        query_vec = get_feature_vector(clip_model, image_bytes=raw)
    else:
        query_vec = get_feature_vector(clip_model, text=query_text)

    query_vec_np = np.array([query_vec]).astype("float32")

    # Step 3：语义向量检索
    top_k = min(50, len(candidates))
    if top_k == 0 or index.ntotal == 0:
        return {"results": []}
        
    distances, ids = search_in_index(index, query_vec_np, top_k)
    semantic_scores = {int(vid): float(1.0 / (dist + 1e-6)) for dist, vid in zip(distances[0], ids[0])}

    # Step 4：混合打分与排序
    if query_text:
        query_tokens = query_text.lower().split()
    else:
        query_tokens = []

    results = []
    for item in candidates:
        base = 0
        if query_tokens:
            item_tags = " ".join(item.get("tags", [])).lower()
            for token in query_tokens:
                if token in item_tags:
                    base += 1.0
        
        semantic = semantic_scores.get(item["vec_id"], 0)
        item["score"] = base + semantic
        results.append(item)

    results.sort(key=lambda x: x["score"], reverse=True)

    return {"results": results}


# ============================================================
# GET /api/items   获取所有物品（用于首页展示）
# ============================================================
@app.get("/api/items")
async def get_all_items_endpoint():
    """
    提供一个接口用于前端获取所有物品列表。
    """
    items = get_all_items()
    # 按时间戳倒序排列，最新的在前面
    sorted_items = sorted(items, key=lambda x: x.get('timestamp', ''), reverse=True)
    return {"results": sorted_items}


# ============================================================
# GET /api/images/{filename}  返回图片
# ============================================================
@app.get("/api/images/{filename}")
async def get_image(filename: str):
    filepath = os.path.join(IMAGE_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, "图片未找到")
    return FileResponse(filepath)


# ============================================================
# 启动服务（开发模式）
# ============================================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)