"""
索引器 —— 管理和更新向量索引。

负责：
  - 增量添加新文档
  - 删除过期文档
  - 重建索引
"""

from typing import Optional

from agent.retrieval.vectorstore import VectorStore
from agent.retrieval.embedder import Embedder


class Indexer:
    """索引管理器。"""

    def __init__(self, vector_store: VectorStore, embedder: Embedder):
        self.vector_store = vector_store
        self.embedder = embedder

    async def add_documents(self, texts: list[str], metadatas: Optional[list[dict]] = None) -> list[str]:
        """向量化并添加到索引。"""
        ...

    async def remove_documents(self, ids: list[str]) -> None:
        """从索引中删除。"""
        ...

    async def rebuild(self) -> None:
        """重建整个索引。"""
        ...
