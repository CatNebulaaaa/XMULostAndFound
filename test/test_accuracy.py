# test_accuracy_v3.py (最终公平测试版)

import os
import json
import csv
import random
import numpy as np
from PIL import Image
from tqdm import tqdm
import requests
from pycocotools.coco import COCO

from feature_extractor import load_models, get_feature_vector
from retrieval_engine import build_or_load_index, add_to_index, search_in_index, save_index
from data_manager import _save_database, get_all_items, add_item

# --- 配置区 ---
COCO_IMAGES_DIR = "coco_val2017"
COCO_ANNOTATIONS_FILE = "annotations/captions_val2017.json"
DB_SIZE = 1000
TEST_QUERIES = 200
TOP_K_VALUES = [1, 5, 10]
TEST_DB_PATH = "test_database.json"
TEST_INDEX_PATH = "test_vectors.index"


def download_coco_setup():
    # (此函数无变化)
    if not os.path.exists(COCO_ANNOTATIONS_FILE):
        print("错误：COCO 标注文件 'annotations/captions_val2017.json' 不存在。")
        exit()
    if not os.path.exists(COCO_IMAGES_DIR):
        os.makedirs(COCO_IMAGES_DIR)
    print(f"正在加载 COCO 标注...")
    coco = COCO(COCO_ANNOTATIONS_FILE)
    img_ids = coco.getImgIds()
    print(f"检查 {DB_SIZE} 张 COCO 图片样本是否存在...")
    for i in tqdm(range(DB_SIZE)):
        img_info = coco.loadImgs(img_ids[i])[0]
        file_path = os.path.join(COCO_IMAGES_DIR, img_info['file_name'])
        if not os.path.exists(file_path):
            try:
                response = requests.get(img_info['coco_url'], stream=True)
                response.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            except Exception as e:
                print(f"下载失败 {img_info['coco_url']}: {e}")
    return coco


def setup_test_environment(clip_model, coco_api):
    """构建测试环境 (已升级为公平模式)"""
    print("\n--- 1. 正在构建测试环境 (公平模式) ---")
    if os.path.exists(TEST_DB_PATH): os.remove(TEST_DB_PATH)
    if os.path.exists(TEST_INDEX_PATH): os.remove(TEST_INDEX_PATH)
    _save_database([], db_path=TEST_DB_PATH)
    index = build_or_load_index(np.zeros((0, 512)).astype("float32"), TEST_INDEX_PATH)
    
    print(f"正在从COCO数据集中提取特征并构建索引库 (共 {DB_SIZE} 项)...")
    for i in tqdm(range(DB_SIZE)):
        img_id = coco_api.getImgIds()[i]
        img_info = coco_api.loadImgs(img_id)[0]
        anns = coco_api.loadAnns(coco_api.getAnnIds(imgIds=img_id))
        captions = [ann['caption'].strip() for ann in anns]
        
        # --- 关键修改：只用一个描述来注册物品 ---
        # 随机选择一个描述作为“注册信息”
        registered_description = random.choice(captions)
        # tags 也只能从这一个描述中生成，杜绝信息泄露
        tags = list(set(registered_description.lower().split()))

        img_path = os.path.join(COCO_IMAGES_DIR, img_info['file_name'])
        if not os.path.exists(img_path): continue
        with open(img_path, 'rb') as f:
            raw_bytes = f.read()
            
        vector = get_feature_vector(clip_model=clip_model, image_bytes=raw_bytes)
        vec_id = index.ntotal
        add_to_index(index, np.array([vector], dtype="float32"))
        
        add_item(
            vec_id=vec_id,
            description=registered_description, # 使用单一的注册描述
            image_filename=img_info['file_name'],
            tags=tags, # 使用从单一描述生成的tags
            location="测试地点",
            category="测试分类",
            db_path=TEST_DB_PATH
        )
    save_index(index, TEST_INDEX_PATH)
    print("测试环境构建完成！")
    return index

# (intelligent_search 和 keyword_only_search 函数无变化)
def intelligent_search(query_text, clip_model, index, all_items):
    query_vec = get_feature_vector(clip_model, text=query_text)
    query_vec_np = np.array([query_vec]).astype("float32")

    distances, ids = search_in_index(index, query_vec_np, n=min(100, index.ntotal)) # 可以多召回一些候选
    
    # --- 关键修改开始 ---

    # 1. 提取原始分数
    semantic_scores_raw = {int(vid): 1.0 / (dist + 1e-9) for dist, vid in zip(distances[0], ids[0])}
    keyword_scores_raw = {}
    query_tokens = query_text.lower().split()
    for item in all_items:
        keyword_scores_raw[item['vec_id']] = sum(1.0 for token in query_tokens if token in " ".join(item.get("tags", [])))

    # 2. 归一化：将两种分数分别缩放到 0-1 区间
    max_semantic = max(semantic_scores_raw.values()) if semantic_scores_raw else 1.0
    max_keyword = max(keyword_scores_raw.values()) if keyword_scores_raw else 1.0
    
    # 防止除以零
    if max_semantic == 0: max_semantic = 1.0
    if max_keyword == 0: max_keyword = 1.0

    semantic_scores_norm = {vid: score / max_semantic for vid, score in semantic_scores_raw.items()}
    keyword_scores_norm = {vid: score / max_keyword for vid, score in keyword_scores_raw.items()}

    # 3. 加权融合
    alpha = 0.7  # <--- 这是超参数，代表语义分的权重，可以调整！
    
    results = []
    for item in all_items:
        vec_id = item['vec_id']
        # 使用 .get(vec_id, 0) 来处理没有出现在语义搜索结果中的物品
        norm_s = semantic_scores_norm.get(vec_id, 0) 
        norm_k = keyword_scores_norm.get(vec_id, 0)
        
        final_score = (alpha * norm_s) + ((1 - alpha) * norm_k)
        item["score"] = final_score
        results.append(item)
    
    # --- 关键修改结束 ---
    
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

def keyword_only_search(query_text, all_items):
    results = []
    query_tokens = set(query_text.lower().split())
    for item in all_items:
        item_tags = set(item.get("tags", []))
        item["score"] = float(len(query_tokens.intersection(item_tags)))
        results.append(item)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def main():
    print("--- 0. 初始化模型与数据 ---")
    clip_model, _ = load_models()
    coco = download_coco_setup()
    
    index = setup_test_environment(clip_model, coco)
    all_items = get_all_items(db_path=TEST_DB_PATH)
    
    print(f"\n--- 2. 开始评估 ({TEST_QUERIES} 个查询) ---")
    evaluation_results = []
    test_items_indices = random.sample(range(len(all_items)), TEST_QUERIES)

    for item_index in tqdm(test_items_indices):
        item_to_find = all_items[item_index]
        ground_truth_vec_id = item_to_find['vec_id']
        registered_description = item_to_find['description']
        
        img_filename = item_to_find['image_filename']
        img_id = int(img_filename.split('.')[0])
        ann_ids = coco.getAnnIds(imgIds=img_id)
        anns = coco.loadAnns(ann_ids)
        all_captions = [ann['caption'] for ann in anns]

        # --- 关键修改：从剩余的描述中选择查询 ---
        other_captions = [c for c in all_captions if c != registered_description]
        if not other_captions:
            # 如果碰巧只有一个描述，就跳过这个测试用例
            continue
        query = random.choice(other_captions)

        intel_results = intelligent_search(query, clip_model, index, all_items)
        keyword_results = keyword_only_search(query, all_items)
        try:
            intel_rank = [r['vec_id'] for r in intel_results].index(ground_truth_vec_id) + 1
        except ValueError: intel_rank = -1
        try:
            keyword_rank = [r['vec_id'] for r in keyword_results].index(ground_truth_vec_id) + 1
        except ValueError: keyword_rank = -1
        
        evaluation_results.append({
            "query": query, "ground_truth_vec_id": ground_truth_vec_id,
            "intelligent_search_rank": intel_rank, "keyword_only_search_rank": keyword_rank,
        })

    # (分析与输出结果逻辑无变化)
    print("\n--- 3. 分析与输出结果 ---")
    accuracies = {"intelligent_search": {k: 0 for k in TOP_K_VALUES}, "keyword_only_search": {k: 0 for k in TOP_K_VALUES}}
    for result in evaluation_results:
        for k in TOP_K_VALUES:
            if 0 < result["intelligent_search_rank"] <= k: accuracies["intelligent_search"][k] += 1
            if 0 < result["keyword_only_search_rank"] <= k: accuracies["keyword_only_search"][k] += 1
    
    query_count = len(evaluation_results)
    print("\n================== 准确率报告 (V3 - 公平盲考) ==================")
    for k in TOP_K_VALUES:
        intel_acc = (accuracies["intelligent_search"][k] / query_count) * 100
        keyword_acc = (accuracies["keyword_only_search"][k] / query_count) * 100
        print(f"Top-{k} 准确率:\n  - 智能搜索: {intel_acc:.2f}%\n  - 关键词搜索: {keyword_acc:.2f}%\n" + "-"*20)
    print("==============================================================")

    csv_file = "evaluation_results_v3.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=evaluation_results[0].keys())
        writer.writeheader()
        writer.writerows(evaluation_results)
    print(f"\n详细结果已保存到 {csv_file}")


if __name__ == "__main__":
    main()