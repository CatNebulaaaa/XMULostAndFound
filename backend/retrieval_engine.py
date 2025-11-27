import os
import faiss
import numpy as np
from typing import List, Tuple


def build_or_load_index(vectors: np.ndarray, index_path: str) -> faiss.Index:
    """
    构建或加载FAISS索引。
    """
    if os.path.exists(index_path):
        print(f"Loading existing FAISS index from {index_path}")
        return faiss.read_index(index_path)
    else:
        print("Building new FAISS index.")
        
        # === 修改开始 ===
        # 原来的代码在这里判断 len(vectors) == 0 就报错，导致无法初始化空库
        # 我们现在只判断 vectors 是否为 None
        if vectors is None:
            raise ValueError("Vectors cannot be None.")
            
        # 获取维度 (例如 512)
        # 即使 vectors 是 (0, 512) 的空数组，shape[1] 依然是 512，这是合法的
        vector_dim = vectors.shape[1]

        # 创建索引
        index = faiss.IndexFlatL2(vector_dim)
        
        # 只有当向量里真的有数据时，才执行 add
        if len(vectors) > 0:
            index.add(vectors)
        # === 修改结束 ===
        
        return index


def save_index(index: faiss.Index, index_path: str) -> None:
    """
    将内存中的FAISS索引保存到硬盘。
    - 参数 index: 需要保存的FAISS索引对象。
    - 参数 index_path: 保存路径。
    """
    print(f"Saving FAISS index to {index_path}")
    faiss.write_index(index, index_path)


def search_in_index(
    index: faiss.Index, query_vector: np.ndarray, n: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    在FAISS索引中执行搜索。
    - 参数 index: 已加载的FAISS索引对象。
    - 参数 query_vector: NumPy数组形式的查询向量 (形状应为 1 x dim)。
    - 参数 n: 希望返回的结果数量。
    - 返回: (距离数组, 索引ID数组)
    """
    if not query_vector.flags["C_CONTIGUOUS"]:
        query_vector = np.ascontiguousarray(query_vector)

    return index.search(query_vector, n)


def add_to_index(index: faiss.Index, vector: np.ndarray) -> None:
    """
    向索引中增量添加一个向量。
    - 参数 index: 需要更新的FAISS索引对象。
    - 参数 vector: NumPy数组形式的新向量 (形状应为 1 x dim)。
    """
    if not vector.flags["C_CONTIGUOUS"]:
        vector = np.ascontiguousarray(vector)

    index.add(vector)
