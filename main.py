from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse
import uvicorn
import numpy as np

# === 依赖：假设所有模块都与 main.py 同级 ===
from feature_extractor import load_models, get_feature_vector, get_tags_from_image
from data_manager import get_all_items, add_item, filter_items, get_item_by_vec_id
from retrieval_engine import (
    build_or_load_index,
    search_in_index,
    add_to_index,
    save_index
)

import os
import uuid

app = FastAPI()

# =========================================
# 全局模型与索引初始化
# =========================================
IMAGE_DIR = "images"
INDEX_PATH = "vectors.index"

# 加载模型（CLIP 与 OCR）
clip_model, ocr_model = load_models()

# 确保图片目录存在
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# 获取数据库已有向量（假设 data_manager 会自己从 json 读）
items = get_all_items()
if len(items) > 0:
    # 假设每个 item 中保存 vec_id 且向量顺序不乱
    initial_vectors = [item["vector"] for item in items]
    index = build_or_load_index(np.array(initial_vectors).astype("float32"), INDEX_PATH)
else:
    # 空向量索引
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
):
    # -----------------------------
    # 1. 保存图片
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
        # image → vector
        vector = get_feature_vector(
            clip_model=clip_model,
            image_bytes=raw_bytes,
            text=None
        )

        # OCR + 云视觉标签
        tags = get_tags_from_image(
            ocr_model=ocr_model,
            image_bytes=raw_bytes,
            api_key="DUMMY_KEY",
            secret_key="DUMMY_SECRET"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"特征提取失败: {str(e)}")

    # -----------------------------
    # 3. 写入向量索引
    # -----------------------------
    vector_np = np.array([vector], dtype="float32")
    # 新向量在索引中的 ID
    vec_id = index.ntotal
    add_to_index(index, vector_np)
    save_index(index, INDEX_PATH)

    # -----------------------------
    # 4. 写入 database.json
    # -----------------------------
    new_item = add_item(
        vec_id=vec_id,
        description=description,
        location=location,
        category=category,
        image_filename=filename,
        tags=tags
    )

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
    # ============================
    # Step 1：先进行元数据过滤
    # ============================
    candidates = filter_items(
        location=location,
        category=category,
        date_range_start=date_range_start,
        date_range_end=date_range_end
    )

    if len(candidates) == 0:
        return {"results": []}

    # ============================
    # Step 2：生成查询向量（文本 or 图片）
    # ============================
    if query_text is None and query_image is None:
        raise HTTPException(400, "query_text 和 query_image 至少提供一个")

    if query_image:
        raw = await query_image.read()
        query_vec = get_feature_vector(clip_model, image_bytes=raw)
    else:
        query_vec = get_feature_vector(clip_model, text=query_text)

    query_vec_np = np.array([query_vec]).astype("float32")

    # ============================
    # Step 3：语义向量检索
    # ============================
    top_k = min(50, len(candidates))
    distances, ids = search_in_index(index, query_vec_np, top_k)

    # ids[0] 是 vec_id 列表
    semantic_scores = {int(vid): float(1.0 / (dist + 1e-6)) for dist, vid in zip(distances[0], ids[0])}

    # ============================
    # Step 4：关键词基础分
    # ============================
    if query_text:
        query_tokens = query_text.lower().split()
    else:
        query_tokens = []

    results = []

    for item in candidates:
        base = 0

        # 命中 OCR / 图像标签 → 给基础分
        if query_tokens:
            item_tags = " ".join(item.get("tags", [])).lower()
            for token in query_tokens:
                if token in item_tags:
                    base += 1.0

        # vec_id 对应语义分
        semantic = semantic_scores.get(item["vec_id"], 0)

        final_score = base + semantic

        item["score"] = final_score
        results.append(item)

    # 排序
    results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "results": results
    }


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
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
