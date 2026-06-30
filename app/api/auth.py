"""API Key 验证中间件 — 简单的请求头校验"""

import logging

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings

logger = logging.getLogger("kb-assistant.auth")

# 无需鉴权的路径白名单
_SKIP_PATHS = {
    "/api/health",
    "/",           # 静态首页
    "/favicon.ico",
}


class APIKeyMiddleware(BaseHTTPMiddleware):
    """检查 X-API-Key 请求头"""

    async def dispatch(self, request: Request, call_next):
        # 未配置 API Key → 跳过校验（本地开发模式）
        if not settings.app_api_key:
            return await call_next(request)

        # 白名单路径跳过
        path = request.url.path
        if path in _SKIP_PATHS or path.startswith("/css") or path.startswith("/js"):
            return await call_next(request)

        # 仅校验 /api 路径
        if not path.startswith("/api"):
            return await call_next(request)

        # 验证 X-API-Key
        client_key = request.headers.get("X-API-Key", "")
        if client_key != settings.app_api_key:
            logger.warning("API Key 校验失败 — %s %s", request.method, path)
            raise HTTPException(status_code=401, detail="无效或缺失 API Key")

        return await call_next(request)
