"""
Agent State 定义 —— 整个 Agent 图共享的状态结构。

包含：
  - messages:      对话消息列表
  - context:       strategist 产出的上下文包（摘要 + 检索结果 + 其他）
  - session_id:    当前会话标识
  - metadata:      额外状态（token 计数、步骤信息等）
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgentState:
    """Agent 图的全局状态。"""
    messages: list[Any] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    session_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
