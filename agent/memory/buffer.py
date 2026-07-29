"""
滑动窗口 (Sliding Window) 记忆策略。

保留最近 N 轮对话（或固定 Token 数），超出部分丢弃。
是所有更复杂策略的 fallback 基础。

每个 session 独立存储，结构：
  _store[session_id] = [msg1, msg2, ...]
"""

from typing import Any, Optional

from agent.memory.base import BaseMemory


class BufferMemory(BaseMemory):
    """基于滑动窗口的短期记忆。"""

    def __init__(self, max_turns: int = 20, max_tokens: int = 4000, priority: int = 50):
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self.priority = priority
        # session_id → list[dict]
        self._store: dict[str, list[dict]] = {}

    @property
    def name(self) -> str:
        return "buffer"

    # ── BaseMemory 接口 ──

    async def add(self, session_id: str, message: Any) -> None:
        """记录一条消息（1 轮 = user + assistant = 2 条消息）。"""
        if session_id not in self._store:
            self._store[session_id] = []

        # 统一转 dict
        if isinstance(message, dict):
            msg = message
        elif hasattr(message, "dict"):
            msg = message.dict()
        else:
            msg = {"content": str(message)}

        msg["_stored_at"] = len(self._store[session_id])  # 顺序标记
        self._store[session_id].append(msg)

        # 滑动窗口裁剪：max_turns 是"轮数"，每轮 2 条消息（user + assistant）
        max_messages = self.max_turns * 2
        if len(self._store[session_id]) > max_messages:
            self._store[session_id] = self._store[session_id][-max_messages:]

    async def get_context(self, session_id: str, query: str) -> Optional[str]:
        """以纯文本形式返回最近对话历史。"""
        messages = self._store.get(session_id, [])
        if not messages:
            return None

        lines = []
        for msg in messages:
            role = msg.get("role", msg.get("type", "unknown"))
            content = msg.get("content", "")
            # 跳过工具调用细节（太长且不必要）
            if role == "tool":
                content = f"[工具返回: {str(content)[:80]}...]" if len(str(content)) > 80 else f"[工具返回: {content}]"
            lines.append(f"{role}: {content}")

        return "\n\n".join(lines)

    async def clear(self, session_id: str) -> None:
        """清理指定会话的记忆。"""
        self._store.pop(session_id, None)

    # ── ContextStrategy 兼容方法 ──

    async def collect(self, session_id: str, query: str) -> Optional[dict[str, Any]]:
        """以策略片段形式返回（用于 pipeline 编排）。"""
        content = await self.get_context(session_id, query)
        if not content:
            return None
        return {
            "priority": self.priority,
            "content": content,
            "tokens": len(content) // 4,  # 粗略估算
        }
