"""
API 请求 / 响应 Schema 定义。
"""

from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    """聊天请求体。"""
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    """聊天响应（非流式模式）。"""
    reply: str


class ResetRequest(BaseModel):
    """重置请求体。"""
    session_id: Optional[str] = "default"


class ResetResponse(BaseModel):
    """重置响应。"""
    status: str = "ok"
