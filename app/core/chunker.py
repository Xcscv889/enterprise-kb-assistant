"""文档分块器 — 段落感知 + 重叠窗口"""

from config import settings


class DocumentChunker:
    def __init__(self, chunk_size: int = None, overlap: int = None):
        self.chunk_size = chunk_size or settings.chunk_size
        self.overlap = overlap or settings.chunk_overlap

    def chunk(self, text: str, doc_id: str, filename: str) -> list[dict]:
        """将文本按段落边界分割为重叠块"""
        # 第一阶段：按双换行（段落）分割
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        chunks = []
        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            # 如果当前块加上新段落不超过限制，直接追加
            if not current_chunk:
                current_chunk = para
            elif len(current_chunk) + len(para) + 2 <= self.chunk_size:
                current_chunk += "\n\n" + para
            else:
                # 当前块已满，保存并开始新块
                if current_chunk:
                    chunks.append(current_chunk)
                    # 重叠：保留当前块末尾部分作为下一个块的起始上下文
                    if self.overlap > 0 and len(current_chunk) > self.overlap:
                        overlap_text = current_chunk[-self.overlap:]
                        current_chunk = overlap_text + "\n\n" + para
                    else:
                        current_chunk = para

        # 保存最后一块
        if current_chunk:
            chunks.append(current_chunk)

        # 处理超长段落：按固定大小拆分
        final_chunks = []
        for chunk_text in chunks:
            if len(chunk_text) <= self.chunk_size * 1.2:
                final_chunks.append(chunk_text)
            else:
                # 按句子边界进一步拆分
                sub_chunks = self._split_long_chunk(chunk_text)
                final_chunks.extend(sub_chunks)

        # 组装带元数据的块
        result = []
        for i, chunk_text in enumerate(final_chunks):
            result.append({
                "text": chunk_text,
                "metadata": {
                    "doc_id": doc_id,
                    "filename": filename,
                    "chunk_index": i,
                    "char_count": len(chunk_text),
                },
            })

        return result

    def _split_long_chunk(self, text: str) -> list[str]:
        """将超长块按句子边界拆分"""
        # 按句号、问号、感叹号、换行等拆分为句子
        import re
        sentences = re.split(r'(?<=[。！？\n])\s*', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        current = ""
        for sent in sentences:
            if len(current) + len(sent) <= self.chunk_size:
                current += sent
            else:
                if current:
                    chunks.append(current.strip())
                current = sent
        if current:
            chunks.append(current.strip())

        return chunks if chunks else [text]
