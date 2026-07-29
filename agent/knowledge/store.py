"""
知识库存储管理 —— CRUD 操作。

负责将处理后的文档存入检索层，并提供元数据管理。
"""

from typing import Optional

from agent.retrieval.indexer import Indexer


class KnowledgeStore:
    """知识库管理器。"""

    def __init__(self, indexer: Indexer):
        self.indexer = indexer

    async def add_document(self, content: str, metadata: Optional[dict] = None) -> list[str]:
        """添加单篇文档。"""
        ...

    async def remove_document(self, doc_id: str) -> None:
        """删除文档。"""
        ...

    async def list_documents(self) -> list[dict]:
        """列出所有文档元信息。"""
        ...

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        """搜索知识库。"""
        ...
