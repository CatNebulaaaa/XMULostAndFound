import os
import faiss
import numpy as np
from typing import List, Tuple


def build_or_load_index(vectors: np.ndarray, index_path: str) -> faiss.Index:
    """
    构建或加载FAISS索引。
    - 参数 vectors: NumPy数组, 用于首次构建索引。
    - 参数 index_path: 索引文件的路径, 用于加载或保存。
    """
    if os.path.exists(index_path):
        print(f"Loading existing FAISS index from {index_path}")
        return faiss.read_index(index_path)
    else:
        print("Building new FAISS index.")
        # 从输入的vectors数组中获取向量维度
        if vectors is None or len(vectors) == 0:
            raise ValueError(
                "Cannot build a new index with an empty or None vector set."
            )
        vector_dim = vectors.shape[1]

        # 我们使用 IndexFlatL2，它执行精确的L2距离搜索。
        index = faiss.IndexFlatL2(vector_dim)
        index.add(vectors)
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
