"""
摘要记忆 (Summary Memory) 策略。

定期将早期对话压缩为摘要，保留「摘要 + 最近 N 轮原文」。
"""

from typing import Any, Optional

from agent.memory.base import BaseMemory


class SummaryMemory(BaseMemory):
    """摘要记忆。"""

    def __init__(self, summary_llm=None, summary_interval: int = 5):
        self.summary_llm = summary_llm
        self.summary_interval = summary_interval

    async def add(self, session_id: str, message: Any) -> None:
        ...

    async def get_context(self, session_id: str, query: str) -> Optional[str]:
        ...

    async def clear(self, session_id: str) -> None:
        ...

    async def _generate_summary(self, session_id: str) -> str:
        """触发摘要生成。"""
        return ""
