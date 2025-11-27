from sentence_transformers import SentenceTransformer
from easyocr import Reader
from PIL import Image
from typing import List, Tuple, Optional
import io
import requests
import base64
import numpy as np
import os  

def load_models() -> Tuple[SentenceTransformer, Reader]:
    """
    加载模型：配置为优先从本地文件夹加载
    """
    print("正在初始化 AI 模型...")
    
    # --- 1. 加载 CLIP 模型 (从本地路径) ---
    clip_model_path = './models/clip-ViT-B-32' # 确保这个路径相对于你运行脚本的位置是正确的
    print(f"1. 正在从本地路径加载 CLIP 模型: {clip_model_path}")
    
    if not os.path.exists(clip_model_path):
        print(f"错误：找不到本地 CLIP 模型路径 '{clip_model_path}'！")
        print("请确认模型文件已放置在正确的位置。")
        exit() # 直接退出程序
        
    clip_model = SentenceTransformer(clip_model_path)
    
    print("CLIP 模型加载完成！")

    # --- 2. 加载 OCR 模型 (从本地路径) ---
    # 为 EasyOCR 指定一个存放模型的文件夹，避免它去网上下载
    ocr_model_path = './models/easyocr' 
    print(f"2. 正在配置 EasyOCR 模型路径: {ocr_model_path}")
    
    # 确保目录存在
    if not os.path.exists(ocr_model_path):
        print(f"警告：找不到本地 EasyOCR 模型路径 '{ocr_model_path}'。将尝试创建文件夹。")
        os.makedirs(ocr_model_path)

    # model_storage_directory: 指定模型下载和读取的目录
    # download_enabled=False: 禁止从网络下载，因为我们已经手动提供了模型
    ocr_model = Reader(
        ['en', 'ch_sim'], 
        gpu=False, 
        model_storage_directory=ocr_model_path,
        download_enabled=False 
    )
    
    print("OCR 模型加载完成！")
    print("所有模型加载完毕！")
    return clip_model, ocr_model

# 下面的函数保持不变...

def get_feature_vector(
    clip_model: SentenceTransformer,
    image_bytes: Optional[bytes] = None,
    text: Optional[str] = None
) -> List[float]:
    """
    将图片或文本转换为特征向量。
    """
    if image_bytes is not None:
        image = Image.open(io.BytesIO(image_bytes))
        feature_vector = clip_model.encode(image, convert_to_numpy=True)
    elif text is not None:
        feature_vector = clip_model.encode(text, convert_to_numpy=True)
    else:
        raise ValueError("必须提供 image_bytes 或 text 参数之一")
    
    return feature_vector.tolist()


def get_tags_from_image(
    ocr_model: Reader,
    image_bytes: bytes,
    api_key: str, 
    secret_key: str
) -> List[str]:
    """
    1. 使用 EasyOCR 识别文字
    2. 使用 百度智能云 识别物体标签
    """
    tags = []
    
    try:
        result = ocr_model.readtext(image_bytes, detail=0)
        if result:
            tags.extend(result)
    except Exception as e:
        print(f"OCR识别出错: {e}")
    
    if not api_key or api_key == "DUMMY_KEY":
        return list(set(tags))

    try:
        token_url = "https://aip.baidubce.com/oauth/2.0/token"
        token_params = {"grant_type": "client_credentials", "client_id": api_key, "client_secret": secret_key}
        token_resp = requests.post(token_url, params=token_params).json()
        access_token = token_resp.get("access_token")

        if access_token:
            detect_url = f"https://aip.baidubce.com/rest/2.0/image-classify/v2/advanced_general?access_token={access_token}"
            img_b64 = base64.b64encode(image_bytes).decode('utf-8')
            payload = {"image": img_b64}
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            resp = requests.post(detect_url, data=payload, headers=headers)
            result_json = resp.json()
            
            if "result" in result_json:
                for item in result_json["result"]:
                    if keyword := item.get("keyword"):
                        tags.append(keyword)
    except Exception as e:
        print(f"云服务调用出错: {e}")
    
    return list(set(tags))