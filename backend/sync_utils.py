# backend/sync_utils.py
import os
from huggingface_hub import HfApi, snapshot_download

# 配置你的仓库信息
REPO_ID = "CatNebulaaa/XMULostAndFound"  
REPO_TYPE = "dataset"
LOCAL_DIR = "." # 当前目录

def pull_data(token: str):
    """启动时：把云端数据拉下来"""
    if not token:
        print("警告 (pull_data): 未提供 token，跳过数据同步。")
        return

    print("正在从 Hugging Face Dataset 同步数据...")
    try:
        snapshot_download(
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            local_dir=LOCAL_DIR,
            token=token,  # 使用传入的 token
            # 只下载我们需要的文件
            allow_patterns=["database.json", "vectors.index", "images/*"],
            ignore_patterns=[".gitattributes", "README.md"]
        )
        print("数据同步完成！")
    except Exception as e:
        print(f"首次启动或同步失败 (可能是第一次运行，属于正常现象): {e}")

def push_data(token: str, filepath: str):
    """
    上传单个文件到云端
    token: 用于认证的 Hugging Face Token
    filepath: 例如 'database.json' 或 'images/abc.jpg'
    """
    if not token:
        print(f"警告 (push_data): 未提供 token，无法上传文件 {filepath}。")
        return

    api = HfApi()
    try:
        print(f"正在备份 {filepath} 到云端...")
        api.upload_file(
            path_or_fileobj=filepath,
            path_in_repo=filepath,
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            token=token  # 使用传入的 token
        )
        print("备份成功！")
    except Exception as e:
        print(f"备份失败: {e}")
        # 抛出异常，让上层调用者知道发生了错误
        raise e