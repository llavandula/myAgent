"""
依赖注入 —— 管理 Session 与 Agent 实例的生命周期。
"""

from typing import Any

# 运行时会被替换为真正的 agent.get_agent()
_session_registry: dict[str, Any] = {}


def get_agent_for_session(session_id: str) -> Any:
    """获取或创建指定 Session 的 Agent 实例。"""
    if session_id not in _session_registry:
        # TODO: 实际从 agent/core.py 创建
        pass
    return _session_registry.get(session_id)


def reset_session(session_id: str) -> None:
    """重置指定 Session。"""
    _session_registry.pop(session_id, None)
