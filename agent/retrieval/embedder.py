"""
Embedding 模型封装 —— 文本 → 向量。

支持：
  - OpenAI Embeddings (text-embedding-3-small / 3-large)
  - 本地模型 (sentence-transformers)
  - DeepSeek / 其他兼容 API
"""

from abc import ABC, abstractmethod


class Embedder(ABC):
    """向量化抽象。"""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """将文本列表转为向量。"""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量维度。"""
        ...
