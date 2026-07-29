"""
检索器 —— query → 处理 → top-K 文档。

支持策略：
  - 纯向量相似度搜索
  - 混合检索（向量 + BM25 关键词）
  - 重排序 (Re-ranking)
"""

from typing import Any, Optional

from agent.retrieval.vectorstore import VectorStore
from agent.retrieval.embedder import Embedder


class Retriever:
    """统一检索入口。"""

    def __init__(self, vector_store: VectorStore, embedder: Embedder):
        self.vector_store = vector_store
        self.embedder = embedder

    async def retrieve(self, query: str, top_k: int = 5, filters: Optional[dict] = None) -> list[dict[str, Any]]:
        """语义检索：query → embedding → 向量搜索。"""
        ...

    async def hybrid_retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """混合搜索（向量 + 关键词），后续实现。"""
        ...
