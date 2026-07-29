"""
混合记忆 (Hybrid Memory) 策略。

组合多种记忆策略，按优先级和 Token Budget 拼装最终上下文。

组合顺序：
  1. 固定上下文（System Prompt / 知识库）
  2. RAG 检索结果
  3. 摘要记忆
  4. 实体记忆
  5. 滑动窗口（最近 N 轮原文）
"""

from typing import Any, Optional

from agent.memory.base import BaseMemory
from agent.memory.buffer import BufferMemory
from agent.memory.summary import SummaryMemory
from agent.memory.entity import EntityMemory


class HybridMemory(BaseMemory):
    """混合记忆 —— 组合 Buffer + Summary + Entity + RAG。"""

    def __init__(
        self,
        buffer: Optional[BufferMemory] = None,
        summary: Optional[SummaryMemory] = None,
        entity: Optional[EntityMemory] = None,
        retriever=None,  # agent/retrieval/retriever.py 的实例
    ):
        self.buffer = buffer or BufferMemory()
        self.summary = summary
        self.entity = entity
        self.retriever = retriever

    async def add(self, session_id: str, message: Any) -> None:
        ...

    async def get_context(self, session_id: str, query: str) -> Optional[str]:
        ...

    async def clear(self, session_id: str) -> None:
        ...
