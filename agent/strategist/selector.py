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
        if not candidates:
            return ""

        # 1. 按优先级降序排列
        sorted_candidates = sorted(candidates, key=lambda x: x["priority"], reverse=True)

        # 2. 在预算内选择性保留
        selected = []
        total_tokens = 0

        for c in sorted_candidates:
            tokens = c.get("tokens", self.estimate_tokens(c["content"]))
            if total_tokens + tokens > self.max_tokens:
                continue  # 超预算，丢弃
            selected.append(c["content"])
            total_tokens += tokens

        return "\n\n".join(selected)

    def estimate_tokens(self, text: str) -> int:
        """粗略估算 token 数（4 chars ≈ 1 token）。"""
        return len(text) // 4
