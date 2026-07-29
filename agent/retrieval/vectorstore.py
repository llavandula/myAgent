"""
向量库封装 —— 统一向量存储接口。

支持后端：
  - Chroma（本地快速原型）
  - FAISS（高性能本地检索）
  - PGVector / Qdrant（生产环境）
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class VectorStore(ABC):
    """向量存储抽象。"""

    @abstractmethod
    async def add(self, texts: list[str], embeddings: list[list[float]], metadata: Optional[list[dict]] = None) -> list[str]:
        """添加文本及其向量到存储。返回 IDs。"""
        ...

    @abstractmethod
    async def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        """按向量相似度搜索。返回 {content, score, metadata}。"""
        ...

    @abstractmethod
    async def delete(self, ids: list[str]) -> None:
        """按 ID 删除。"""
        ...
