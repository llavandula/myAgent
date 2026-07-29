"""
编排流水线 —— 组合多种策略，产出最终上下文包。

工作流程：
  1. 遍历注册的所有 ContextStrategy
  2. 每个策略收集自己的上下文片段
  3. ContextSelector 按 Token Budget 裁剪
  4. 拼接成 ContextPackage 返回
"""

from typing import Any, Optional

from agent.strategist.base import ContextStrategy
from agent.strategist.selector import ContextSelector
from agent.strategist.compressor import ContextCompressor
from agent.schemas import ContextPackage


class ContextPipeline:
    """上下文编排流水线。"""

    def __init__(
        self,
        strategies: Optional[list[ContextStrategy]] = None,
        selector: Optional[ContextSelector] = None,
        compressor: Optional[ContextCompressor] = None,
    ):
        self.strategies = strategies or []
        self.selector = selector or ContextSelector()
        self.compressor = compressor

    def register(self, strategy: ContextStrategy) -> None:
        """注册一个策略。"""
        self.strategies.append(strategy)

    async def build(self, session_id: str, query: str) -> ContextPackage:
        """执行流水线，产出上下文包。"""
        candidates = []
        for strategy in self.strategies:
            ctx = await strategy.collect(session_id, query)
            if ctx and ctx.get("content"):
                candidates.append(ctx)

        selected = self.selector.select(candidates)

        if self.compressor and len(selected) > 2000:
            selected = await self.compressor.compress(selected, query)

        return ContextPackage(recent_history=[selected])
