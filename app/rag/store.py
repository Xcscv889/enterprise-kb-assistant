"""ChromaDB 向量存储 — 集合管理、文档 CRUD"""

from uuid import uuid4

import chromadb

from config import settings


class VectorStore:
    """管理 ChromaDB 持久化向量存储"""

    def __init__(self, persist_dir: str = None, embedding_service=None):
        persist_dir = persist_dir or settings.chroma_persist_dir
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=chromadb.Settings(anonymized_telemetry=False),
        )
        self.embedding_service = embedding_service

        # 初始化集合
        self.doc_collection = self._get_or_create(
            settings.chroma_collection_docs,
            metadata={"hnsw:space": "cosine"},
        )
        self.memory_collection = self._get_or_create(
            settings.chroma_collection_memory,
            metadata={"hnsw:space": "cosine"},
        )

    def _get_or_create(self, name: str, metadata: dict = None):
        try:
            return self.client.get_collection(name)
        except Exception:
            return self.client.create_collection(
                name=name,
                metadata=metadata or {},
            )

    # ── 文档块操作 ──

    def add_chunks(self, chunks: list) -> int:
        """嵌入并存储文档块，返回存储数量"""
        if not chunks:
            return 0

        texts = [c["text"] for c in chunks]
        embeddings = self.embedding_service.encode(texts)
        ids = [uuid4().hex for _ in chunks]
        metadatas = [c.get("metadata", {}) for c in chunks]

        self.doc_collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas,
        )
        return len(chunks)

    def delete_by_document_id(self, doc_id: str) -> int:
        """按文档 ID 删除所有关联块"""
        try:
            results = self.doc_collection.get(where={"doc_id": doc_id})
            if results["ids"]:
                self.doc_collection.delete(ids=results["ids"])
            return len(results["ids"])
        except Exception:
            return 0

    def list_documents(self) -> list[dict]:
        """列出已索引的文档汇总信息"""
        try:
            results = self.doc_collection.get(include=["metadatas"])
        except Exception:
            return []

        doc_map: dict[str, dict] = {}
        for meta in (results.get("metadatas") or []):
            if meta is None:
                continue
            doc_id = meta.get("doc_id", "unknown")
            if doc_id not in doc_map:
                doc_map[doc_id] = {
                    "id": doc_id,
                    "filename": meta.get("filename", "unknown"),
                    "chunks": 0,
                }
            doc_map[doc_id]["chunks"] += 1

        return list(doc_map.values())

    # ── 记忆操作 ──

    def add_memory_fact(self, fact: str, session_id: str, metadata: dict = None) -> str:
        """存储一条长期记忆事实"""
        embedding = self.embedding_service.encode_query(fact)
        fact_id = uuid4().hex
        meta = metadata or {}
        meta.update({"session_id": session_id, "type": "long_term_fact"})
        self.memory_collection.add(
            ids=[fact_id],
            embeddings=[embedding.tolist()],
            documents=[fact],
            metadatas=[meta],
        )
        return fact_id

    def query_memory(self, query_embedding, session_id: str, n_results: int = 3):
        """查询与 query 相关的长期记忆"""
        try:
            return self.memory_collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                where={"session_id": session_id},
                include=["documents", "distances"],
            )
        except Exception:
            return {"documents": [[]], "distances": [[]]}

    def delete_memory_by_session(self, session_id: str) -> int:
        """清除某个会话的所有长期记忆"""
        try:
            results = self.memory_collection.get(where={"session_id": session_id})
            if results["ids"]:
                self.memory_collection.delete(ids=results["ids"])
            return len(results["ids"])
        except Exception:
            return 0
