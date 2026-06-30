# ── 企业知识库AI助手 Docker 镜像 ──
FROM python:3.11-slim

# 系统依赖：PyMuPDF 需要 libgl1，其他为通用编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── 先复制依赖文件，利用 Docker 缓存层 ──
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ── 预热嵌入模型（首次启动时不需要再下载） ──
RUN python -c "\
from fastembed import TextEmbedding; \
print('>> 正在下载嵌入模型 BAAI/bge-small-zh-v1.5 ...'); \
m = TextEmbedding(model_name='BAAI/bge-small-zh-v1.5'); \
vec = list(m.embed(['预热'])); \
print('>> 模型预热完成，向量维度:', len(vec[0])) \
"

# ── 复制应用代码 ──
COPY app/ ./app/
COPY static/ ./static/
COPY config.py main.py ./

# 确保运行时目录存在（实际数据通过 volume 挂载）
RUN mkdir -p uploads chroma_data

EXPOSE 8000

# ── 启动 ──
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
