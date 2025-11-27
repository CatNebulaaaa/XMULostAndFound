# tuning_vs_keyword.py

import os
import csv
import random
import numpy as np
from tqdm import tqdm
from pycocotools.coco import COCO

# 确保可以从同级目录导入你的模块
from feature_extractor import load_models, get_feature_vector
from retrieval_engine import build_or_load_index, add_to_index, search_in_index, save_index
from data_manager import _save_database, get_all_items, add_item

# --- 配置区 ---
DB_SIZE = 1000         # 数据库大小
TEST_QUERIES = 200     # 测试查询数量

COCO_IMAGES_DIR = "coco_val2017"
COCO_ANNOTATIONS_FILE = "annotations/captions_val2017.json"
TOP_K_VALUES = [1, 5, 10]
TEST_DB_PATH = "test_database.json"
TEST_INDEX_PATH = "test_vectors.index"

# --- 超参数搜索空间 ---
ALPHAS_TO_TEST = [0.0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

# (intelligent_search, keyword_only_search, setup_test_environment, download_coco_setup 等函数无需修改)
def intelligent_search(query_text, clip_model, index, all_items, alpha=0.8):
    query_vec = get_feature_vector(clip_model, text=query_text)
    query_vec_np = np.array([query_vec]).astype("float32")
    distances, ids = search_in_index(index, query_vec_np, n=min(100, index.ntotal))
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
    
    print(f"\n--- 正在生成 {TEST_QUERIES} 个固定的测试查询 ---")
    test_queries = []
    test_items_indices = random.sample(range(len(all_items)), TEST_QUERIES)
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

    tuning_report = []
    
    # --- 关键修改：预先计算一次关键词搜索的基准准确率 ---
    print("\n--- 正在计算关键词搜索的基准准确率 ---")
    keyword_accuracies = {k: 0 for k in TOP_K_VALUES}
    for test_case in tqdm(test_queries):
        keyword_results = keyword_only_search(test_case['query'], all_items)
        try:
            rank = [r['vec_id'] for r in keyword_results].index(test_case['ground_truth_vec_id']) + 1
            for k in TOP_K_VALUES:
                if rank <= k: keyword_accuracies[k] += 1
        except ValueError:
            pass
    
    query_count = len(test_queries)
    keyword_final_accuracies = {k: (v / query_count) * 100 for k, v in keyword_accuracies.items()}
    
    # --- 开始超参数搜索循环 ---
    for alpha in ALPHAS_TO_TEST:
        print(f"\n--- 2. 正在使用 alpha = {alpha:.2f} 进行评估 ---")
        
        intelligent_accuracies = {k: 0 for k in TOP_K_VALUES}
        for test_case in tqdm(test_queries):
            intel_results = intelligent_search(test_case['query'], clip_model, index, all_items, alpha=alpha)
            try:
                rank = [r['vec_id'] for r in intel_results].index(test_case['ground_truth_vec_id']) + 1
                for k in TOP_K_VALUES:
                    if rank <= k: intelligent_accuracies[k] += 1
            except ValueError:
                pass

        intelligent_final_accuracies = {k: (v / query_count) * 100 for k, v in intelligent_accuracies.items()}
        
        # --- 关键修改：将两种结果都记录下来 ---
        report_entry = {'alpha': alpha}
        for k in TOP_K_VALUES:
            report_entry[f'Intelligent_Top-{k}_Acc(%)'] = intelligent_final_accuracies[k]
            report_entry[f'Keyword_Top-{k}_Acc(%)'] = keyword_final_accuracies[k] # 关键词准确率对所有alpha都是一样的
        tuning_report.append(report_entry)

    # --- 3. 输出最终总结报告 ---
    print("\n\n=============================== 超参数搜索 vs 关键词基准 ===============================")
    print("alpha\tIntel Top-1(%)\tKeyw Top-1(%)\tIntel Top-5(%)\tKeyw Top-5(%)\tIntel Top-10(%)\tKeyw Top-10(%)")
    print("-----\t--------------\t--------------\t--------------\t--------------\t---------------\t---------------")
    
    best_entry = max(tuning_report, key=lambda x: x['Intelligent_Top-1_Acc(%)'])
    
    for entry in tuning_report:
        is_best_str = "  <-- BEST" if entry['alpha'] == best_entry['alpha'] else ""
        print(f"{entry['alpha']:.2f}\t"
              f"{entry['Intelligent_Top-1_Acc(%)']:.2f}\t\t"
              f"{entry['Keyword_Top-1_Acc(%)']:.2f}\t\t"
              f"{entry['Intelligent_Top-5_Acc(%)']:.2f}\t\t"
              f"{entry['Keyword_Top-5_Acc(%)']:.2f}\t\t"
              f"{entry['Intelligent_Top-10_Acc(%)']:.2f}\t\t"
              f"{entry['Keyword_Top-10_Acc(%)']:.2f}"
              f"{is_best_str}")
    print("==========================================================================================")

    csv_file = "tuning_vs_keyword_results.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=tuning_report[0].keys())
        writer.writeheader()
        writer.writerows(tuning_report)
    print(f"\n详细对比报告已保存到 {csv_file}")

if __name__ == "__main__":
    main()