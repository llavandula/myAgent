"""
LangGraph 图定义 —— Agent 的执行流。

节点 (Nodes):
  - prep_context: 注入拼装好的上下文包（来自 strategist/pipeline）
  - agent:        LLM 推理、决定是否调用工具
  - tools:        执行工具调用
  - memorize:     本轮归档 & 摘要 / Embedding 更新

边 (Edges):
  - agent → tools    (当 LLM 产生 tool_call 时)
  - agent → memorize (当 LLM 直接回复时)
  - tools → agent    (工具结果回传后继续推理)
"""

from typing import Any


def create_graph() -> Any:
    """构建并返回编译好的 LangGraph (CompiledStateGraph)。

    当前返回占位值 None，后续实现。
    """
    return None
