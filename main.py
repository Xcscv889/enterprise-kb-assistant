"""企业知识库AI助手 — FastAPI 应用入口"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from config import settings

# 确保数据目录存在
Path("./uploads").mkdir(parents=True, exist_ok=True)
Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时加载模型和组件，关闭时清理资源"""
    print("[启动] 正在加载嵌入模型...")
    from app.core.embedding import EmbeddingService
    app.state.embedding_service = EmbeddingService(
        model_name=settings.embedding_model_name,
        device=settings.embedding_device,
    )
    print(f"[启动] 嵌入模型已加载 (维度: {app.state.embedding_service.dim})")

    print("[启动] 正在连接 ChromaDB...")
    from app.rag.store import VectorStore
    app.state.vector_store = VectorStore(
        persist_dir=settings.chroma_persist_dir,
        embedding_service=app.state.embedding_service,
    )
    print("[启动] ChromaDB 已连接")

    print("[启动] 正在初始化 LLM 客户端...")
    from app.core.llm_client import LLMClient
    app.state.llm_client = LLMClient()

    print("[启动] 正在初始化解析器...")
    from app.parsing.parser_registry import create_parser_registry
    app.state.parser_registry = create_parser_registry()

    print("[启动] 正在初始化记忆模块...")
    from app.memory.conversation import ConversationMemory
    from app.memory.long_term import LongTermMemory
    app.state.conversation_memory = ConversationMemory()
    app.state.long_term_memory = LongTermMemory(
        vector_store=app.state.vector_store,
        embedding_service=app.state.embedding_service,
        llm_client=app.state.llm_client,
    )

    # 后台清理任务
    async def cleanup_loop():
        while True:
            await asyncio.sleep(300)  # 每 5 分钟
            app.state.conversation_memory.cleanup_expired()

    cleanup_task = asyncio.create_task(cleanup_loop())

    print("[启动] 企业知识库AI助手已就绪!")
    yield

    # 关闭
    cleanup_task.cancel()
    print("[关闭] 应用已停止")


app = FastAPI(
    title="企业知识库AI助手",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 允许本地开发
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API 路由 ──
from app.api.health import router as health_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.memory import router as memory_router

app.include_router(health_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(memory_router, prefix="/api")

# ── 静态文件 (必须放在最后) ──
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    # reload=False: Windows 下单进程运行，Ctrl+C 能干净退出，不会残留僵尸进程
    # 开发时如需热重载，改回 reload=True，但每次 Ctrl+C 后留意端口是否释放
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
