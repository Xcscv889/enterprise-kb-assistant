"""PDF 解析器 — 使用 PyMuPDF 提取文本"""

import fitz  # PyMuPDF


class PDFParser:
    extension = ".pdf"

    def parse(self, file_path: str) -> str:
        """提取 PDF 全部文本，保留段落结构"""
        doc = fitz.open(file_path)
        parts = []
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if text.strip():
                parts.append(text.strip())
        doc.close()

        if not parts:
            return "（此 PDF 无可提取文本，可能为扫描件）"

        return "\n\n".join(parts)
