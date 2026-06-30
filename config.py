"""集中配置管理 — 从 .env 文件和环境变量加载"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── 应用鉴权 ──
    app_api_key: str = ""  # 为空则跳过 API Key 校验（本地开发）；设置后所有 /api/* 请求需带 X-API-Key 头

    # ── DeepSeek API ──
    deepseek_api_key: str = ""  # 请通过 .env 文件或环境变量设置
    deepseek_base_url: str = ""
    deepseek_model: str = "deepseek-chat"
    deepseek_temperature: float = 0.1
    deepseek_max_tokens: int = 2048

    # ── 嵌入模型 ──
    embedding_model_name: str = "BAAI/bge-small-zh-v1.5"
    embedding_device: str = "cpu"

    # ── ChromaDB ──
    chroma_persist_dir: str = "./chroma_data"
    chroma_collection_docs: str = "enterprise_docs"
    chroma_collection_memory: str = "long_term_memory"

    # ── 文档分块 ──
    chunk_size: int = 800
    chunk_overlap: int = 150

    # ── 检索 ──
    retrieval_top_k: int = 5
    retrieval_distance_threshold: float = 0.6

    # ── 记忆 ──
    short_term_max_messages: int = 20
    short_term_ttl_seconds: int = 3600
    long_term_synthesis_interval: int = 5
    long_term_max_age_days: int = 90

    # ── 上传 ──
    max_upload_size_mb: int = 50
    allowed_extensions: list[str] = [".pdf", ".docx", ".txt", ".md"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
