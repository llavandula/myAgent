"""
共享 Pydantic 模型。

用于各层之间的数据传输和校验。
"""

from pydantic import BaseModel
from typing import Any, Optional


class MemoryEntry(BaseModel):
    """一条记忆记录。"""
    session_id: str
    content: str
    metadata: dict[str, Any] = {}


class RetrievalResult(BaseModel):
    """一次检索命中结果。"""
    content: str
    score: float
    source: str = ""


class ContextPackage(BaseModel):
    """strategist 最终产出的上下文包。"""
    summary: Optional[str] = None
    recent_history: list[str] = []
    retrieved_docs: list[RetrievalResult] = []
    entities: dict[str, str] = {}
