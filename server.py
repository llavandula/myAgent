"""
FastAPI 后端 —— 将 Agent 暴露为 HTTP + SSE 流式 API。

入口文件，保持薄。后续路由逻辑可迁移到 api/routes.py。

启动:
    python server.py
    访问 http://localhost:8000
"""

import json
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from agent.core import get_agent

app = FastAPI(title="Agent Chat")

# 每个会话一个 agent 实例（生产环境应换成 Redis 等）
sessions: dict[str, object] = {}

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_or_create_agent(session_id: str):
    """为每个 session 创建独立的 agent 实例，互不干扰。"""
    if session_id not in sessions:
        agent_graph, _, _ = get_agent()
        sessions[session_id] = agent_graph
    return sessions[session_id]


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", encoding="utf-8") as f:
        return f.read()


@app.post("/chat")
async def chat(request: Request):
    """
    SSE 流式对话接口。

    前端发送: { "message": "...", "session_id": "..." }
    服务端返回 SSE 事件流，每条事件格式:
        event: tool_call
        data: {"tool": "xxx", "args": {...}}

        event: tool_result
        data: {"tool": "xxx", "result": "..."}

        event: text
        data: {"content": "..."}

        event: done
        data: {}
    """
    body = await request.json()
    user_message = body.get("message", "").strip()
    session_id = body.get("session_id", "default")

    if not user_message:
        return StreamingResponse(
            _sse_event("error", {"content": "消息不能为空"}),
            media_type="text/event-stream",
        )

    agent = get_or_create_agent(session_id)
    config = {"configurable": {"thread_id": session_id}}

    async def event_stream():
        try:
            stream_input = {"messages": [{"role": "user", "content": user_message}]}
            prev_text = ""  # 上一次推送的累计文本,用于计算增量

            # 必须用 astream(async for)而非 stream(for),否则同步生成器会
            # 阻塞事件循环,直到整个 agent 跑完才一次性把事件推给前端。
            async for event in agent.astream(stream_input, config=config, stream_mode="messages"):
                if not event:
                    continue

                message, metadata = event
                node = metadata.get("langgraph_node", "")

                if node == "agent":
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tc in message.tool_calls:
                            tool_name = tc.get("name") or ""
                            if not tool_name:
                                continue
                            yield _sse_event("tool_call", {
                                "tool": tool_name,
                                "args": tc.get("args", {}),
                            })
                        # 切到下一段文本,重置基准(避免重复推送)
                        prev_text = ""

                    # 流式文本：只推送"上次没发过"的那部分(增量 token)
                    if hasattr(message, "content") and message.content:
                        text = message.content
                        if isinstance(text, str):
                            if text.startswith(prev_text):
                                delta = text[len(prev_text):]
                                prev_text = text
                                if delta:
                                    yield _sse_event("text", {"content": delta})
                            else:
                                # 异常情况(非累积):整段推送并重置
                                prev_text = text
                                if text.strip():
                                    yield _sse_event("text", {"content": text})

                elif node == "tools":
                    tool_name = message.name if hasattr(message, "name") else "unknown"
                    content = message.content if hasattr(message, "content") else str(message)
                    # 工具结果回来后重置基准,避免后续文本被错判为已发
                    prev_text = ""
                    yield _sse_event("tool_result", {
                        "tool": tool_name,
                        "result": str(content)[:500],
                    })

            yield _sse_event("done", {})

        except Exception as e:
            yield _sse_event("error", {"content": str(e)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/reset")
async def reset(request: Request):
    """重置指定会话。"""
    body = await request.json()
    session_id = body.get("session_id", "default")
    sessions.pop(session_id, None)
    return {"status": "ok"}


def _sse_event(event: str, data: dict) -> str:
    """构造一条 SSE 事件字符串。"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
