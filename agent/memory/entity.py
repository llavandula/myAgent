"""
实体记忆 (Entity Memory) 策略。

从对话中提取命名实体（人名、地点、偏好等）并持久化，
在后续对话中注入 System Prompt。
"""

from typing import Any, Optional

from agent.memory.base import BaseMemory


class EntityMemory(BaseMemory):
    """实体记忆。"""

    def __init__(self, extraction_llm=None):
        self.extraction_llm = extraction_llm

    async def add(self, session_id: str, message: Any) -> None:
        ...

    async def get_context(self, session_id: str, query: str) -> Optional[str]:
        ...

    async def clear(self, session_id: str) -> None:
        ...

    async def _extract_entities(self, text: str) -> dict[str, str]:
        """从一段文本中提取实体。"""
        return {}
