"""Pydantic 数据模型"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


# ── 聊天请求 / 响应 ──

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4096, description="用户提问")
    session_id: str = Field(default_factory=gen_id, description="会话 ID")


class SourceInfo(BaseModel):
    filename: str
    page: Optional[int] = None
    chunk_id: Optional[str] = None
    score: float = 0.0


class ChatDoneEvent(BaseModel):
    type: str = "done"
    sources: list[SourceInfo] = []
    session_id: str = ""


# ── 文档 ──

class DocumentInfo(BaseModel):
    id: str
    filename: str
    chunks: int
    size_bytes: int
    uploaded_at: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_count: int
    status: str


class DeleteResponse(BaseModel):
    status: str
    document_id: str
    chunks_removed: int


# ── 记忆 ──

class MemoryInfo(BaseModel):
    session_id: str
    short_term: dict
    long_term: dict


class MemoryClearResponse(BaseModel):
    status: str
    session_id: str


# ── 聊天历史 ──

class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[dict]
    count: int


class SessionListItem(BaseModel):
    session_id: str
    turn_count: int
    last_accessed: str = ""
