from sentence_transformers import SentenceTransformer
from easyocr import Reader
from PIL import Image
from typing import List, Tuple, Optional
import io
import requests
import base64
import numpy as np


def load_models() -> Tuple[SentenceTransformer, Reader]:
    """
    同时加载CLIP和EasyOCR模型,在服务启动时调用一次。
    Returns: Tuple[SentenceTransformer, Reader]
    """
    clip_model = SentenceTransformer('clip-ViT-B-32')
    
    ocr_model = Reader(['en', 'ch_sim'], gpu=True)
    
    return clip_model, ocr_model


def get_feature_vector(
    clip_model: SentenceTransformer,
    image_bytes: Optional[bytes] = None,
    text: Optional[str] = None
) -> List[float]:
    """
    将图片或文本转换为特征向量。
    - 参数 clip_model: 已加载的CLIP模型对象,避免重复加载。
    - 参数 image_bytes: 图片的二进制內容,用于图片特征提取。
    - 参数 text: 文本字符串,用于文本特征提取。
    
    Returns: List[float]: 特征向量
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
    从图片中识别文字。
    - 参数 ocr_model: 已加载的EasyOCR模型对象。
    - 参数 image_bytes: 图片的二进制内容。
    调用云服务API,从图片中识别物体的视觉特征标签。
    - 参数 image_bytes: 图片的二进制內容,用于API请求。
    - 参数 api_key/secret_key: 调用API所需的认证凭据。
    - 返回值:一个由识别出的标签组成的字符串列表。
    
    Returns: List[str]: 识别出的标签列表
    """
    tags = []
    
    # 1. 使用EasyOCR进行文字识别
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image_np = np.array(image)
        
        ocr_results = ocr_model.readtext(image_np)
        
        for detection in ocr_results:
            text = detection[1]  # detection格式: (bbox, text, confidence)
            if text:
                tags.append(text)
    except Exception as e:
        print(f"OCR识别出错: {e}")
    
    # 2. 调用云服务API识别视觉特征标签
    try:
        # 将图片转换为base64编码
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # 以下是一个示例结构，实际使用时需要根据具体API文档调整
        api_url = "https://api.example.com/v1/image/analyze"  # 替换为实际API地址
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # 构建请求体
        payload = {
            "image": image_base64,
            "api_key": api_key,
            "secret_key": secret_key
        }
        
        # 发送API请求
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            # 根据实际API响应格式解析标签
            if "tags" in result:
                tags.extend(result["tags"])
            elif "labels" in result:
                tags.extend(result["labels"])
        else:
            print(f"API调用失败，状态码: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"API请求出错: {e}")
    except Exception as e:
        print(f"视觉特征识别出错: {e}")
    
    return list(set(tags)) if tags else []