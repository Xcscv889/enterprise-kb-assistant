"""文档管理 API — 上传、列表、删除"""

import os
import time
import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse

from config import settings
from app.core.chunker import DocumentChunker
from app.models.schemas import (
    UploadResponse, DocumentInfo, DocumentListResponse, DeleteResponse, gen_id,
)
from app.parsing.parser_registry import UnsupportedFileTypeError

router = APIRouter(tags=["documents"])

# 文档元数据存储（简单 dict，生产环境可换数据库）
_document_meta: dict[str, dict] = {}


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(request: Request, file: UploadFile = File(...)):
    """上传并索引文档"""
    # 验证文件类型
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型 {ext}，支持: {', '.join(settings.allowed_extensions)}",
        )

    # 验证文件大小
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.max_upload_size_mb:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小 {size_mb:.1f}MB 超过限制 {settings.max_upload_size_mb}MB",
        )

    # 保存临时文件
    doc_id = gen_id()
    upload_dir = Path("./uploads")
    safe_filename = f"{doc_id}_{file.filename}"
    file_path = upload_dir / safe_filename

    with open(file_path, "wb") as f:
        f.write(content)

    try:
        # 解析文档
        parser_registry = request.app.state.parser_registry
        text = parser_registry.parse_file(str(file_path))

        if not text or len(text.strip()) < 10:
            raise HTTPException(status_code=400, detail="文档内容过短，无法提取有效文本")

        # 分块
        chunker = DocumentChunker()
        chunks = chunker.chunk(text, doc_id=doc_id, filename=file.filename)

        if not chunks:
            raise HTTPException(status_code=400, detail="文档分块失败")

        # 存入向量数据库
        vector_store = request.app.state.vector_store
        vector_store.add_chunks(chunks)

        # 记录元数据
        _document_meta[doc_id] = {
            "id": doc_id,
            "filename": file.filename,
            "chunks": len(chunks),
            "size_bytes": len(content),
            "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        return UploadResponse(
            document_id=doc_id,
            filename=file.filename,
            chunks_count=len(chunks),
            status="indexed",
        )

    except UnsupportedFileTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")
    finally:
        # 清理临时文件
        if file_path.exists():
            file_path.unlink()


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(request: Request):
    """列出所有已索引的文档"""
    vector_store = request.app.state.vector_store
    docs = vector_store.list_documents()

    # 合并元数据
    for doc in docs:
        meta = _document_meta.get(doc["id"], {})
        doc.update({
            "size_bytes": meta.get("size_bytes", 0),
            "uploaded_at": meta.get("uploaded_at", "unknown"),
        })

    return DocumentListResponse(
        documents=[
            DocumentInfo(
                id=d["id"],
                filename=d["filename"],
                chunks=d["chunks"],
                size_bytes=d.get("size_bytes", 0),
                uploaded_at=d.get("uploaded_at", "unknown"),
            )
            for d in docs
        ]
    )


@router.delete("/documents/{doc_id}", response_model=DeleteResponse)
async def delete_document(request: Request, doc_id: str):
    """删除文档及其所有向量"""
    vector_store = request.app.state.vector_store
    removed = vector_store.delete_by_document_id(doc_id)
    _document_meta.pop(doc_id, None)

    return DeleteResponse(
        status="deleted",
        document_id=doc_id,
        chunks_removed=removed,
    )
