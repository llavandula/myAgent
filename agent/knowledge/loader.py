"""
文档加载器 —— 支持多种来源。

Input: 文件路径 / URL / 文本
Output: 纯文本 + 元数据
"""

from abc import ABC, abstractmethod
from typing import Any


class DocumentLoader(ABC):
    """文档加载抽象。"""

    @abstractmethod
    async def load(self, source: str) -> list[dict[str, Any]]:
        """加载文档，返回 [{content, metadata}]。"""
        ...

    @abstractmethod
    async def load_batch(self, sources: list[str]) -> list[list[dict[str, Any]]]:
        """批量加载。"""
        ...


class TextFileLoader(DocumentLoader):
    """加载 .txt / .md 文件。"""

    async def load(self, source: str) -> list[dict[str, Any]]:
        ...

    async def load_batch(self, sources: list[str]) -> list[list[dict[str, Any]]]:
        ...


class PDFLoader(DocumentLoader):
    """加载 PDF 文件。"""

    async def load(self, source: str) -> list[dict[str, Any]]:
        ...

    async def load_batch(self, sources: list[str]) -> list[list[dict[str, Any]]]:
        ...
