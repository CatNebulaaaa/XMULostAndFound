import os
import random
import string
import requests
import time

# ================= 配置区域 =================
# 你的后端上传接口
API_URL = "https://catnebulaaa-xmulostandfound.hf.space/api/items"

# 本地存放图片的文件夹名称
IMAGE_DIR = "images"

# 地点列表
LOCATIONS = [
    '翔安校区-德旺图书馆',
    '翔安校区-主楼群（坤銮/文宣/学武/1号楼）',
    '翔安校区-一期食堂',
    '翔安校区-二期食堂',
    '翔安校区-学生公寓（芙蓉/凌云/国光）',
    '翔安校区-学生活动中心',
    '思明校区-图书馆总馆',
    '思明校区-嘉庚楼群',
    '思明校区-芙蓉餐厅',
    '思明校区-勤业餐厅',
    '思明校区-南光/芙蓉/石井宿舍区',
    '思明校区-上弦场/建南大会堂'
]

# ================= 辅助函数 =================

def generate_random_contact():
    """生成一个随机的联系方式字符串，例如: User_a1b2c3"""
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    return f"User_{random_str}"

def process_upload():
    # 1. 检查文件夹是否存在
    if not os.path.exists(IMAGE_DIR):
        print(f"❌ 错误：找不到文件夹 '{IMAGE_DIR}'，请先创建并放入图片。")
        return

    # 2. 获取所有图片文件
    supported_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')
    files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(supported_extensions)]

    if not files:
        print(f"⚠️ 文件夹 '{IMAGE_DIR}' 是空的，没有找到图片。")
        return

    print(f"🚀 发现 {len(files)} 张图片，准备开始批量上传...\n")

    success_count = 0
    fail_count = 0

    # 3. 遍历上传
    for index, filename in enumerate(files):
        file_path = os.path.join(IMAGE_DIR, filename)
        
        # 构造随机数据
        payload = {
            "description": "测试物品",
            "location": random.choice(LOCATIONS), # 随机选一个地点
            "category": "其他",
            "contact": generate_random_contact(), # 随机生成联系方式
            "item_type": random.choice(["found", "lost"]) # 随机选 lost 或 found
        }

        print(f"[{index+1}/{len(files)}] 正在上传 {filename} ... ", end="")

        try:
            with open(file_path, "rb") as f:
                # 构造文件参数
                files_data = {"file": f}
                
                # 发送请求
                response = requests.post(API_URL, data=payload, files=files_data)

                if response.status_code == 200:
                    print("✅ 成功")
                    success_count += 1
                else:
                    print(f"❌ 失败 ({response.status_code})")
                    # print(response.text) # 如果想看详细错误可以取消注释
                    fail_count += 1

        except Exception as e:
            print(f"❌ 出错: {e}")
            fail_count += 1
        
        # 可选：稍微停顿一下，避免请求太快把服务器冲垮（Hugging Face CPU有限）
        # time.sleep(0.5) 

    print("\n" + "="*30)
    print(f"🎉 任务结束！")
    print(f"成功: {success_count} 张")
    print(f"失败: {fail_count} 张")
    print("="*30)
    print("👉 现在去刷新你的前端网页，应该能看到所有图片了！")

if __name__ == "__main__":
    process_upload()