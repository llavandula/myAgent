"""
编排流水线 —— 组合多种策略，产出最终上下文包。

工作流程：
  1. 遍历注册的所有策略
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
        strategies: Optional[list[Any]] = None,
        selector: Optional[ContextSelector] = None,
        compressor: Optional[ContextCompressor] = None,
    ):
        # strategies 支持任何实现了 collect() + name 的对象
        self.strategies: list[Any] = strategies or []
        self.selector = selector or ContextSelector()
        self.compressor = compressor

    def register(self, strategy: Any) -> None:
        """注册一个策略（需要实现 collect() 和 name）。"""
        self.strategies.append(strategy)

    async def build(self, session_id: str, query: str) -> ContextPackage:
        """执行流水线，产出上下文包。"""
        if not self.strategies:
            return ContextPackage()

        # 1. 逐一收集上下文片段
        candidates = []
        for strategy in self.strategies:
            try:
                ctx = await strategy.collect(session_id, query)
                if ctx and ctx.get("content"):
                    ctx.setdefault("priority", 50)
                    ctx.setdefault("tokens", len(ctx["content"]) // 4)
                    ctx["_source"] = getattr(strategy, "name", "unknown")
                    candidates.append(ctx)
            except Exception as e:
                # 单个策略失败不影响整体
                import sys
                print(f"[pipeline] strategy {getattr(strategy, 'name', '?')} failed: {e}", file=sys.stderr)
                continue

        if not candidates:
            return ContextPackage()

        # 2. Token Budget 裁剪
        selected = self.selector.select(candidates)

        # 3. 可选压缩
        if self.compressor and len(selected) > 2000:
            selected = await self.compressor.compress(selected, query)

        package = ContextPackage()
        if selected:
            package.recent_history = [selected]

        return package

    async def store_message(self, session_id: str, role: str, content: str) -> None:
        """存储一条消息到所有注册的记忆策略（记忆策略需实现 BaseMemory.add）。"""
        for strategy in self.strategies:
            add = getattr(strategy, "add", None)
            if add:
                await add(session_id, {"role": role, "content": content})
