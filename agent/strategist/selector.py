"""
上下文选择器 —— Token Budget 裁剪。

按优先级从高到低排列上下文片段，
在达到 Token 上限时丢弃低优先级内容。
"""

from typing import Any


class ContextSelector:
    """Token Budget 控制器。"""

    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens

    def select(self, candidates: list[dict[str, Any]]) -> str:
        """按优先级从高到低选择，直到填满 max_tokens。

        candidates: [{ "priority": int, "content": str, "tokens": int }]
        返回拼接后的上下文文本。
        """
        ...

    def estimate_tokens(self, text: str) -> int:
        """粗略估算 token 数（4 chars ≈ 1 token）。"""
        return len(text) // 4
