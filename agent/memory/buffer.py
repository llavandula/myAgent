"""
滑动窗口 (Sliding Window) 记忆策略。

保留最近 N 轮对话（或固定 Token 数），超出部分丢弃。
是所有更复杂策略的 fallback 基础。
"""

from typing import Any, Optional

from agent.memory.base import BaseMemory


class BufferMemory(BaseMemory):
    """基于滑动窗口的短期记忆。"""

    def __init__(self, max_turns: int = 20, max_tokens: int = 4000):
        self.max_turns = max_turns
        self.max_tokens = max_tokens

    async def add(self, session_id: str, message: Any) -> None:
        ...

    async def get_context(self, session_id: str, query: str) -> Optional[str]:
        ...

    async def clear(self, session_id: str) -> None:
        ...
