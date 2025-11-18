import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional

DATABASE_PATH = "database.json"


def _load_database() -> List[Dict]:
    """
    内部函数：从JSON文件加载数据库。如果文件不存在，则返回一个空列表。
    """
    try:
        with open(DATABASE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def _save_database(data: List[Dict]) -> None:
    """
    内部函数：将数据保存到JSON文件。
    """
    with open(DATABASE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_all_items() -> List[Dict]:
    """
    读取并返回数据库中所有物品的元数据。
    """
    return _load_database()


def add_item(
    vec_id: int,
    description: str,
    location: str,
    category: str,
    image_filename: str,
    tags: List[str],
) -> Dict:
    """
    向数据库中添加一条新的物品记录。
    - 参数 vec_id: 整数ID，必须与该物品向量在FAISS索引中的ID严格对应。
    - 其他参数: 物品的各项元数据。
    """
    items = _load_database()

    new_item = {
        "id": str(uuid.uuid4()),  # 生成唯一的字符串ID
        "vec_id": vec_id,
        "description": description,
        "location": location,
        "category": category,
        "image_filename": image_filename,
        "timestamp": datetime.utcnow().isoformat() + "Z",  # 使用ISO 8601格式并标记为UTC
        "tags": tags,
    }

    items.append(new_item)
    _save_database(items)

    return new_item


def filter_items(
    location: Optional[str] = None,
    category: Optional[str] = None,
    date_range_start: Optional[str] = None,
    date_range_end: Optional[str] = None,
) -> List[Dict]:
    """
    根据一个或多个筛选条件过滤物品。
    - 参数: 均为可选的字符串,用于精确或范围匹配。
    """
    items = _load_database()
    filtered_items = []

    # 解析日期范围
    start_date = (
        datetime.fromisoformat(date_range_start.replace("Z", "+00:00"))
        if date_range_start
        else None
    )
    end_date = (
        datetime.fromisoformat(date_range_end.replace("Z", "+00:00"))
        if date_range_end
        else None
    )

    for item in items:
        # 匹配地点
        if location and item.get("location") != location:
            continue
        # 匹配分类
        if category and item.get("category") != category:
            continue
        # 匹配日期范围
        item_date = datetime.fromisoformat(item.get("timestamp").replace("Z", "+00:00"))
        if start_date and item_date < start_date:
            continue
        if end_date and item_date > end_date:
            continue

        filtered_items.append(item)

    return filtered_items


def get_item_by_vec_id(vec_id: int) -> Optional[Dict]:
    """
    通过FAISS返回的vec_id快速查找对应的物品元数据。
    - 参数 vec_id: 整数ID。
    """
    items = _load_database()
    for item in items:
        if item.get("vec_id") == vec_id:
            return item
    return None


def get_next_vec_id() -> int:
    """
    获取下一个可用的 vec_id (即当前存储的物品总数)。
    这对于确保 FAISS 索引的 ID 和元数据 ID 同步至关重要。
    """
    items = _load_database()
    return len(items)
