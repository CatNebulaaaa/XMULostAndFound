# test_recall_impact.py (已修复 ValueError)

import os
import csv
import random
import numpy as np
from tqdm import tqdm
from pycocotools.coco import COCO
import requests

from feature_extractor import load_models, get_feature_vector
from retrieval_engine import build_or_load_index, add_to_index, search_in_index, save_index
from data_manager import _save_database, get_all_items, add_item

# --- 配置区 ---
DB_SIZE = 1000
TEST_QUERIES = 200 # 这是我们“期望”的测试数量

COCO_IMAGES_DIR = "coco_val2017"
COCO_ANNOTATIONS_FILE = "annotations/captions_val2017.json"
TOP_K_VALUES = [1, 5, 10]
FIXED_ALPHA = 0.8
RECALL_NUMBERS_TO_TEST = [10, 25, 50, 100, 200, 500]

TEST_DB_PATH = "test_database.json"
TEST_INDEX_PATH = "test_vectors.index"

# (intelligent_search, keyword_only_search, setup_test_environment, download_coco_setup 等辅助函数保持不变)
def intelligent_search(query_text, clip_model, index, all_items, alpha, recall_n):
    query_vec = get_feature_vector(clip_model, text=query_text)
    query_vec_np = np.array([query_vec]).astype("float32")
    distances, ids = search_in_index(index, query_vec_np, n=min(recall_n, index.ntotal))
    semantic_scores_raw = {int(vid): 1.0 / (dist + 1e-9) for dist, vid in zip(distances[0], ids[0])}
    keyword_scores_raw = {}
    query_tokens = query_text.lower().split()
    recalled_item_ids = set(semantic_scores_raw.keys())
    for item in all_items:
        if item['vec_id'] in recalled_item_ids:
            keyword_scores_raw[item['vec_id']] = sum(1.0 for token in query_tokens if token in " ".join(item.get("tags", [])))
    max_semantic = max(semantic_scores_raw.values()) if semantic_scores_raw else 1.0
    max_keyword = max(keyword_scores_raw.values()) if keyword_scores_raw else 1.0
    if max_semantic == 0: max_semantic = 1.0
    if max_keyword == 0: max_keyword = 1.0
    semantic_scores_norm = {vid: score / max_semantic for vid, score in semantic_scores_raw.items()}
    keyword_scores_norm = {vid: score / max_keyword for vid, score in keyword_scores_raw.items()}
    results = []
    for item in all_items:
        vec_id = item['vec_id']
        norm_s = semantic_scores_norm.get(vec_id, 0)
        norm_k = keyword_scores_norm.get(vec_id, 0)
        final_score = (alpha * norm_s) + ((1 - alpha) * norm_k)
        item["score"] = final_score
        results.append(item)
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

def setup_test_environment(clip_model, coco_api):
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
        registered_description = random.choice(captions)
        tags = list(set(registered_description.lower().split()))
        img_path = os.path.join(COCO_IMAGES_DIR, img_info['file_name'])
        if not os.path.exists(img_path): continue
        with open(img_path, 'rb') as f: raw_bytes = f.read()
        vector = get_feature_vector(clip_model=clip_model, image_bytes=raw_bytes)
        vec_id = index.ntotal
        add_to_index(index, np.array([vector], dtype="float32"))
        add_item(vec_id=vec_id, description=registered_description, image_filename=img_info['file_name'],
                   tags=tags, location="测试地点", category="测试分类", db_path=TEST_DB_PATH)
    save_index(index, TEST_INDEX_PATH)
    print("测试环境构建完成！")
    return index

def download_coco_setup():
    if not os.path.exists(COCO_ANNOTATIONS_FILE):
        print(f"错误：COCO 标注文件 '{COCO_ANNOTATIONS_FILE}' 不存在。")
        exit()
    if not os.path.exists(COCO_IMAGES_DIR): os.makedirs(COCO_IMAGES_DIR)
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
                    for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
            except Exception as e: print(f"下载失败 {img_info['coco_url']}: {e}")
    return coco

def main():
    print("--- 0. 初始化模型与数据 ---")
    clip_model, _ = load_models()
    coco = download_coco_setup()
    
    index = setup_test_environment(clip_model, coco)
    all_items = get_all_items(db_path=TEST_DB_PATH)

    # --- 关键修改：确保样本数量不超过总体数量 ---
    actual_population_size = len(all_items)
    if actual_population_size == 0:
        print("错误：数据库为空，无法进行测试。请检查数据准备步骤。")
        return
        
    actual_test_queries_count = min(TEST_QUERIES, actual_population_size)
    print(f"\n--- 数据库中共有 {actual_population_size} 个有效物品，将生成 {actual_test_queries_count} 个固定的测试查询 ---")

    test_queries = []
    test_items_indices = random.sample(range(actual_population_size), actual_test_queries_count)
    # --- 修改结束 ---

    for item_index in test_items_indices:
        item_to_find = all_items[item_index]
        registered_description = item_to_find['description']
        img_id = int(item_to_find['image_filename'].split('.')[0])
        anns = coco.loadAnns(coco.getAnnIds(imgIds=img_id))
        all_captions = [ann['caption'] for ann in anns]
        other_captions = [c for c in all_captions if c != registered_description]
        if not other_captions: continue
        query = random.choice(other_captions)
        test_queries.append({'query': query, 'ground_truth_vec_id': item_to_find['vec_id']})

    # --- 关键修改：在后续计算中使用实际的查询数量 ---
    query_count = len(test_queries)
    if query_count == 0:
        print("错误：未能成功生成任何有效的测试查询。")
        return
    # --- 修改结束 ---

    recall_impact_report = []
    
    print(f"\n--- 正在计算关键词搜索的基准准确率 (基于 {query_count} 个查询) ---")
    keyword_accuracies = {k: 0 for k in TOP_K_VALUES}
    for test_case in tqdm(test_queries):
        keyword_results = keyword_only_search(test_case['query'], all_items)
        try:
            rank = [r['vec_id'] for r in keyword_results].index(test_case['ground_truth_vec_id']) + 1
            for k in TOP_K_VALUES:
                if rank <= k: keyword_accuracies[k] += 1
        except ValueError: pass
    
    keyword_final_accuracies = {k: (v / query_count) * 100 for k, v in keyword_accuracies.items()}
    
    for recall_n in RECALL_NUMBERS_TO_TEST:
        print(f"\n--- 2. 正在使用 Recall N = {recall_n} (alpha={FIXED_ALPHA}) 进行评估 (基于 {query_count} 个查询) ---")
        
        intelligent_accuracies = {k: 0 for k in TOP_K_VALUES}
        for test_case in tqdm(test_queries):
            intel_results = intelligent_search(test_case['query'], clip_model, index, all_items, alpha=FIXED_ALPHA, recall_n=recall_n)
            try:
                rank = [r['vec_id'] for r in intel_results].index(test_case['ground_truth_vec_id']) + 1
                for k in TOP_K_VALUES:
                    if rank <= k: intelligent_accuracies[k] += 1
            except ValueError: pass

        intelligent_final_accuracies = {k: (v / query_count) * 100 for k, v in intelligent_accuracies.items()}
        
        report_entry = {'recall_n': recall_n}
        for k in TOP_K_VALUES:
            report_entry[f'Intelligent_Top-{k}_Acc(%)'] = intelligent_final_accuracies[k]
        recall_impact_report.append(report_entry)

    print("\n\n======================== 召回数量对准确率影响的报告 (alpha=0.8) ========================")
    print("Recall N\tIntel Top-1(%)\tIntel Top-5(%)\tIntel Top-10(%)")
    print("--------\t--------------\t--------------\t---------------")
    print(f"Keyword \t{keyword_final_accuracies[1]:.2f}\t\t{keyword_final_accuracies[5]:.2f}\t\t{keyword_final_accuracies[10]:.2f}\t\t<-- Baseline")
    print("--------\t--------------\t--------------\t---------------")
    for entry in recall_impact_report:
        print(f"{entry['recall_n']}\t\t{entry['Intelligent_Top-1_Acc(%)']:.2f}\t\t{entry['Intelligent_Top-5_Acc(%)']:.2f}\t\t{entry['Intelligent_Top-10_Acc(%)']:.2f}")
    print("==========================================================================================")

    csv_file = "recall_impact_results.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        header = ['recall_n'] + [f'Intelligent_Top-{k}_Acc(%)' for k in TOP_K_VALUES]
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(recall_impact_report)
        keyword_row = {'recall_n': 'keyword_baseline'}
        for k in TOP_K_VALUES: keyword_row[f'Intelligent_Top-{k}_Acc(%)'] = keyword_final_accuracies[k]
        writer.writerow(keyword_row)
    print(f"\n详细对比报告已保存到 {csv_file}")

if __name__ == "__main__":
    main()