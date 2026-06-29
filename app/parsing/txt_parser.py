"""纯文本解析器"""


class TxtParser:
    extension = ".txt"

    def parse(self, file_path: str) -> str:
        """读取纯文本文件，自动检测编码"""
        # 尝试 UTF-8，失败则尝试 GBK
        for encoding in ["utf-8", "gbk", "gb2312", "latin-1"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                return content.strip() if content.strip() else "（文件内容为空）"
            except UnicodeDecodeError:
                continue

        # 最终兜底
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().strip()
