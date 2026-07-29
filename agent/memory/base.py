"""
记忆层抽象接口。

所有记忆策略实现均应继承 BaseMemory。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseMemory(ABC):
    """记忆策略的基类。"""

    @abstractmethod
    async def add(self, session_id: str, message: Any) -> None:
        """记录一条消息。"""
        ...

    @abstractmethod
    async def get_context(self, session_id: str, query: str) -> Optional[str]:
        """根据当前 query 获取该会话相关的记忆上下文。"""
        ...

    @abstractmethod
    async def clear(self, session_id: str) -> None:
        """清理指定会话的记忆。"""
        ...
