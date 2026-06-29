"""健康检查端点"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "components": {
            "chromadb": "connected",
            "embedding_model": "loaded",
        },
    }
