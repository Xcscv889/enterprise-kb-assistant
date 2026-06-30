# 企业知识库AI助手

基于 **RAG（检索增强生成）** 架构的智能企业文档问答系统。上传企业文档（PDF/Word/TXT/Markdown），系统自动解析、向量化存储，支持自然语言提问，结合 DeepSeek 大模型生成精准回答。

---

## 项目任务

为企业构建一个**私有化知识库问答平台**，核心能力：

- 多格式文档智能解析与向量化入库
- 基于语义检索的精准内容召回
- 结合大模型的流式生成式问答
- 短期对话记忆 + 长期知识提取

帮助企业员工快速从海量文档中查找信息，降低知识获取成本。

---

## 快速开始

### 本地开发

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量（复制 .env.example 为 .env 并填写 API Key）
cp .env.example .env

# 3. 启动服务
python main.py

# 4. 浏览器打开
# http://localhost:8000
```

### 🐳 Docker 部署（推荐生产环境）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，填入真实的 DEEPSEEK_API_KEY

# 2. 构建并启动
docker compose up -d --build

# 3. 查看日志确认启动成功
docker compose logs -f

# 4. 浏览器打开
# http://localhost:8000
```

首次构建镜像时会自动下载嵌入模型（约 100MB），后续启动无需等待。

---

## ☁️ 云服务器部署

### 服务器配置要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2 核 | 4 核 |
| 内存 | 4 GB | 8 GB |
| 磁盘 | 20 GB | 40 GB SSD |
| 系统 | Ubuntu 22.04 / Debian 12 | Ubuntu 22.04 |
| 带宽 | 1 Mbps | 5 Mbps |

> 嵌入模型在内存中约占用 200MB，ChromaDB 查询需要额外内存。4GB 是底线。

### 部署步骤

```bash
# 1. SSH 连接云服务器
ssh root@<服务器公网IP>

# 2. 安装 Docker（如未安装）
curl -fsSL https://get.docker.com | bash

# 3. 上传项目代码
#    方式A：git clone <仓库地址>
#    方式B：scp -r 企业知识库AI助手/ root@<IP>:/opt/

cd /opt/企业知识库AI助手

# 4. 配置 API Key
cp .env.example .env
vim .env   # 填入 DEEPSEEK_API_KEY=sk-xxxx

# 5. 构建并启动容器
docker compose up -d --build

# 6. 确认服务运行正常
docker compose logs -f

# 7. 开放防火墙端口
#    阿里云：安全组 → 入方向 → 允许 TCP 8000
#    腾讯云：防火墙 → 添加规则 → TCP 8000
#    AWS：Security Group → Inbound → TCP 8000

# 8. 浏览器访问
# http://<服务器公网IP>:8000
```

### 常用运维命令

```bash
# 查看运行状态
docker compose ps

# 查看实时日志
docker compose logs -f

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 更新代码后重新部署
git pull
docker compose up -d --build

# 数据备份（chroma_data 和 uploads 目录已在宿主机持久化）
tar -czf backup-$(date +%Y%m%d).tar.gz chroma_data/ uploads/
```

### 数据持久化说明

- `chroma_data/`：向量数据库文件，**重启不丢失**
- `uploads/`：上传的原始文档，**重启不丢失**
- 对话记忆：存储在 ChromaDB 中，随 chroma_data 持久化
- 以上目录通过 Docker volume bind mount 挂载到宿主机，与容器生命周期解耦

---

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI + Uvicorn | 异步高性能 HTTP 服务 |
| 大模型 | DeepSeek (OpenAI 兼容) | 流式对话生成 |
| 嵌入模型 | BAAI/bge-small-zh-v1.5 | 本地 ONNX Runtime 推理，无需 GPU |
| 向量数据库 | ChromaDB | 持久化存储文档向量 |
| 文档解析 | PyMuPDF + python-docx | PDF/DOCX/TXT/Markdown 解析 |

---

## 功能特点

### 📄 文档管理
- 支持 **PDF / DOCX / TXT / Markdown** 四种格式上传
- 自动文本提取与智能分块（800 字符/块，150 字符重叠）
- 向量化索引入库，支持文档列表查看与删除

### 🤖 智能问答（RAG）
- **5 阶段 RAG 管道**：查询嵌入 → 记忆检索 → 文档检索 → 上下文组装 → 流式生成
- SSE（Server-Sent Events）流式返回，逐字展示回答
- 无匹配结果时自动降级为纯对话模式

### 🧠 双记忆系统
- **短期记忆**：保存最近 20 轮对话上下文，1 小时 TTL
- **长期记忆**：每 5 轮自动合成关键信息，持久化到 ChromaDB，支持跨会话回忆

### ⚡ 本地嵌入
- 使用 **fastembed (ONNX Runtime)** 本地运行嵌入模型
- 无需安装 PyTorch 或 GPU，CPU 即可高效推理

### 🌐 Web 界面
- 简洁的聊天 UI，支持多会话管理
- 文档上传拖拽交互
- 实时显示回答来源追溯

---

## 项目结构

```
企业知识库AI助手/
├── main.py                 # FastAPI 应用入口
├── config.py               # 集中配置（.env 加载）
├── requirements.txt        # Python 依赖
├── Dockerfile              # Docker 镜像构建
├── docker-compose.yml      # Docker 编排配置
├── .dockerignore           # Docker 构建排除
├── app/
│   ├── api/                # API 路由
│   │   ├── chat.py         # 聊天接口（SSE 流式）
│   │   ├── documents.py    # 文档上传/列表/删除
│   │   ├── memory.py       # 记忆查看/清除
│   │   └── health.py       # 健康检查
│   ├── core/               # 核心组件
│   │   ├── llm_client.py   # DeepSeek LLM 客户端
│   │   ├── embedding.py    # 嵌入模型服务
│   │   ├── chunker.py      # 文档分块器
│   │   └── prompts.py      # 提示词模板
│   ├── rag/                # RAG 检索增强
│   │   ├── pipeline.py     # 管道编排器
│   │   ├── retriever.py    # 文档检索器
│   │   └── store.py        # ChromaDB 向量存储
│   ├── memory/             # 记忆系统
│   │   ├── conversation.py # 短期对话记忆
│   │   └── long_term.py    # 长期记忆合成
│   ├── parsing/            # 文档解析
│   │   ├── parser_registry.py
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   ├── txt_parser.py
│   │   └── markdown_parser.py
│   └── models/             # 数据模型
│       └── schemas.py
├── static/                 # 前端静态文件
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── app.js
│       ├── chat.js
│       └── upload.js
├── uploads/                # 上传文件暂存
└── chroma_data/            # ChromaDB 持久化目录
```
