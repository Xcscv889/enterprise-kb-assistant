"""嵌入模型服务 — 基于 fastembed (ONNX Runtime)，无需 PyTorch"""

import logging
import numpy as np
from fastembed import TextEmbedding

from config import settings

logger = logging.getLogger("kb-assistant.embedding")


class EmbeddingService:
    """本地嵌入模型包装器，使用 ONNX Runtime 推理"""

    def __init__(self, model_name: str = None, device: str = None):
        model_name = model_name or settings.embedding_model_name

        logger.info("加载模型: %s (ONNX Runtime)", model_name)
        self.model = TextEmbedding(
            model_name=model_name,
            cache_dir=None,
        )
        # fastembed 返回列表，取第一条获取维度
        sample = list(self.model.embed(["test"]))[0]
        self.dim = len(sample)
        self.model_name = model_name
        logger.info("模型已就绪 (维度: %d)", self.dim)

    def encode(self, texts: list[str]) -> np.ndarray:
        """批量编码文本为归一化嵌入向量"""
        if not texts:
            return np.array([])
        embeddings = list(self.model.embed(texts))
        arr = np.array(embeddings)

        # L2 归一化（ChromaDB cosine 空间要求）
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # 避免除零
        return arr / norms

    def encode_query(self, text: str) -> np.ndarray:
        """单条查询编码"""
        return self.encode([text])[0]
