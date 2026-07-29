"""
上下文策略抽象接口。

所有策略（Buffer / Summary / Retriever 等）均应实现此接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class ContextStrategy(ABC):
    """策略基类。"""

    @abstractmethod
    async def collect(self, session_id: str, query: str) -> dict[str, Any]:
        """收集该策略产生的上下文片段。

        返回格式：{ "priority": int, "content": str, "tokens": int }
        优先级越高越优先保留。
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称。"""
        ...
