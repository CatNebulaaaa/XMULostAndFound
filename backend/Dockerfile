# 1. 使用官方 Python 3.9 镜像作为基础
FROM python:3.9

# 2. 设置工作目录
WORKDIR /app

# 3. 安装系统级依赖 (EasyOCR 的底层依赖 opencv 需要这个)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 4. 复制依赖清单并安装
COPY requirements.txt .
# 推荐使用 opencv-python-headless 以减小体积并避免 GUI 报错
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 5. 创建非 root 用户 (Hugging Face 安全要求)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# 6. 设置 EasyOCR 和 HuggingFace 的模型缓存目录
# 确保程序有权限往这些目录写文件
ENV EASYOCR_MODULE_PATH=$HOME/app/easyocr_models
ENV TORCH_HOME=$HOME/app/torch_cache
ENV SENTENCE_TRANSFORMERS_HOME=$HOME/app/st_cache

# 创建这些目录
RUN mkdir -p $EASYOCR_MODULE_PATH $TORCH_HOME $SENTENCE_TRANSFORMERS_HOME

# 7. 复制所有代码到容器 (注意设置所有者为 user)
COPY --chown=user . $HOME/app

# 8. 暴露端口 7860 (Hugging Face Space 默认端口)
EXPOSE 7860

# 9. 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]