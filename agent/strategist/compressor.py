"""
上下文压缩器 —— 将冗余或低价值内容压缩为更紧凑的表示。

场景：
  - 将过长的 tool_result 摘要化
  - 将多轮相似对话合并
  - 移除 query 无关内容
"""

from typing import Any, Optional


class ContextCompressor:
    """上下文压缩器。"""

    def __init__(self, compress_llm=None):
        self.compress_llm = compress_llm

    async def compress(self, context: str, query: str, max_tokens: Optional[int] = None) -> str:
        """压缩上下文，保留与 query 最相关的信息。"""
        ...

    def truncate(self, text: str, max_chars: int = 500) -> str:
        """粗暴截断（fallback）。"""
        return text[:max_chars] + "..." if len(text) > max_chars else text
