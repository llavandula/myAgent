"""
数据库 ORM 模型。

主要表：
  - sessions:      会话元信息
  - messages:      全量消息
  - summaries:     对话摘要
  - embeddings:    向量索引（或由 vectorstore 自行管理）
  - entities:      实体记忆
  - knowledge:     知识库文档元信息
"""

from typing import Any


class SessionModel:
    """会话表。"""
    id: str
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = {}


class MessageModel:
    """消息记录表。"""
    id: str
    session_id: str
    role: str  # user / assistant / tool
    content: str
    created_at: str


class SummaryModel:
    """摘要表。"""
    session_id: str
    summary: str
    version: int
    updated_at: str


class EntityModel:
    """实体表。"""
    session_id: str
    entity_key: str
    entity_value: str
    updated_at: str
