"""
文本分割器 —— 将长文本分割为适合 Embedding 和检索的段落。

策略：
  - RecursiveCharacterTextSplitter（等长 + 分隔符优先级）
  - SemanticSplitter（语义边界感知，需后续实现）
"""

from typing import Optional


class TextSplitter:
    """文本分割器。"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, separators: Optional[list[str]] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", "。", ".", " "]

    def split(self, text: str) -> list[str]:
        """将文本分割成块。"""
        ...

    def split_documents(self, docs: list[dict]) -> list[dict]:
        """将 [{content, metadata}] 分割后展平。"""
        ...
