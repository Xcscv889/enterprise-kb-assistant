"""文档解析器注册表 — 文件扩展名到解析器的分发"""

from pathlib import Path


class UnsupportedFileTypeError(Exception):
    def __init__(self, extension: str):
        self.extension = extension
        super().__init__(f"不支持的文件类型: {extension}")


class BaseParser:
    """解析器基类"""
    extension: str = ""

    def parse(self, file_path: str) -> str:
        raise NotImplementedError


class ParserRegistry:
    def __init__(self):
        self._parsers: dict[str, BaseParser] = {}

    def register(self, parser: BaseParser):
        self._parsers[parser.extension] = parser

    def get_parser(self, extension: str) -> BaseParser:
        ext = extension.lower()
        if ext not in self._parsers:
            raise UnsupportedFileTypeError(ext)
        return self._parsers[ext]

    def parse_file(self, file_path: str) -> str:
        ext = Path(file_path).suffix.lower()
        parser = self.get_parser(ext)
        return parser.parse(file_path)

    @property
    def supported_extensions(self) -> list[str]:
        return list(self._parsers.keys())


def create_parser_registry() -> ParserRegistry:
    """工厂函数：创建并注册所有解析器"""
    from app.parsing.pdf_parser import PDFParser
    from app.parsing.docx_parser import DocxParser
    from app.parsing.txt_parser import TxtParser
    from app.parsing.markdown_parser import MarkdownParser

    registry = ParserRegistry()
    registry.register(PDFParser())
    registry.register(DocxParser())
    registry.register(TxtParser())
    registry.register(MarkdownParser())
    return registry
