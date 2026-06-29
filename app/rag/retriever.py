"""ChromaDB 检索器 — 嵌入查询 + 距离阈值过滤"""

from config import settings


class Retriever:
    """向量相似度检索"""

    def __init__(self, vector_store, embedding_service):
        self.store = vector_store
        self.embedding_service = embedding_service
        self.top_k = settings.retrieval_top_k
        self.distance_threshold = settings.retrieval_distance_threshold

    def retrieve(self, query: str) -> list[dict]:
        """检索与查询最相关的文档块"""
        query_embedding = self.embedding_service.encode_query(query)

        try:
            results = self.store.doc_collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=self.top_k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            return []

        chunks = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        for text, meta, dist in zip(docs, metas, dists):
            if dist <= self.distance_threshold:
                chunks.append({
                    "text": text,
                    "filename": meta.get("filename", "unknown") if meta else "unknown",
                    "page": meta.get("page") if meta else None,
                    "chunk_index": meta.get("chunk_index") if meta else None,
                    "doc_id": meta.get("doc_id") if meta else "unknown",
                    "distance": round(dist, 4),
                })

        return chunks
