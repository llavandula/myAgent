"""
API 层 —— FastAPI 路由定义。

负责：
  - HTTP 请求接收与校验
  - 依赖注入（获取 session agent）
  - SSE 流式组装与推送
"""

from agent.strategist.pipeline import ContextPipeline


def create_app(pipeline: ContextPipeline):
    """创建并返回 FastAPI app。后续实现。

    Args:
        pipeline: 上下文编排流水线，由上层注入。
    """
    from fastapi import FastAPI
    return FastAPI(title="Agent Chat")
