"""Markdown 解析器 — 保留代码块等结构化内容"""

import re


class MarkdownParser:
    extension = ".md"

    def parse(self, file_path: str) -> str:
        """解析 Markdown，去除 YAML frontmatter，保留有意义的文本"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 去除 YAML frontmatter
        content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)

        # 去除图片链接 ![alt](url)
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)

        # 保留有内容的行，去除纯标记符号行
        lines = []
        for line in content.split("\n"):
            stripped = line.strip()
            # 跳过空行
            if not stripped:
                if lines and lines[-1] != "":
                    lines.append("")
                continue
            # 保留标题（去掉 # 标记）
            if stripped.startswith("#"):
                clean = re.sub(r'^#+\s*', '', stripped)
                lines.append(clean)
            # 保留列表项
            elif re.match(r'^[\*\-\+]\s', stripped):
                clean = re.sub(r'^[\*\-\+]\s+', '• ', stripped)
                lines.append(clean)
            elif re.match(r'^\d+\.\s', stripped):
                lines.append(stripped)
            # 跳过纯分隔线
            elif re.match(r'^[\-\*\_]{3,}$', stripped):
                continue
            # 跳过 HTML 标签行
            elif stripped.startswith('<') and stripped.endswith('>'):
                continue
            else:
                lines.append(stripped)

        text = "\n".join(lines)
        return text.strip() if text.strip() else "（Markdown 文件内容为空）"
