"""
FastAPI 后端 —— 将 Agent 暴露为 HTTP + SSE 流式 API。

SSE 事件流协议（与前端兼容）：
  event: tool_call     data: {"id":"...", "tool":"...", "args":{...}}
  event: tool_result   data: {"id":"...", "result":"...", "duration":..., "status":"..."}
  event: text          data: {"content":"..."}
  event: done          data: {}
  event: error         data: {"content":"..."}
  event: stopped       data: {}
"""

import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from agent.core import get_agent, create_pipeline
from storage import init_db, repo


# ── 全局状态 ──
# sessions[session_id] = {"agent": ..., "pipeline": ..., "stop_event": asyncio.Event()}
sessions: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭钩子。"""
    await init_db()
    yield
    from storage.db import db
    await db.disconnect()


app = FastAPI(title="Agent Chat", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")


# ============================================================
# 会话管理
# ============================================================

def get_or_create_agent(session_id: str):
    """为每个 session 创建独立的 agent + pipeline + stop_event。"""
    if session_id not in sessions:
        agent_graph = get_agent()
        pipeline = create_pipeline()
        sessions[session_id] = {
            "agent": agent_graph,
            "pipeline": pipeline,
            "stop_event": asyncio.Event(),
        }
    return sessions[session_id]


# ============================================================
# 页面
# ============================================================

@app.get("/")
async def index():
    from fastapi.responses import HTMLResponse
    with open("static/index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())


# ============================================================
# 对话（SSE 流式）
# ============================================================

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_message = body.get("message", "").strip()
    session_id = body.get("session_id", "default")

    if not user_message:
        return StreamingResponse(_sse_gen("error", {"content": "消息不能为空"}), media_type="text/event-stream")

    session = get_or_create_agent(session_id)
    agent_graph = session["agent"]
    pipeline = session["pipeline"]
    stop_event = session["stop_event"]
    stop_event.clear()  # 重置停止标记

    async def event_stream():
        try:
            # ── 前置：写入用户消息并构建上下文 ──
            await pipeline.store_message(session_id, "user", user_message)
            context_pkg = await pipeline.build(session_id, user_message)
            context_str = context_pkg.recent_history[0] if context_pkg.recent_history else ""

            messages = []
            if context_str:
                messages.append({"role": "system", "content": f"以下是本对话之前的历史：\n{context_str}"})
            messages.append({"role": "user", "content": user_message})

            stream_input = {"messages": messages}
            prev_text = ""
            full_ai_response = ""
            tool_starts: dict[str, float] = {}
            has_any_output = False

            async for event in agent_graph.astream(stream_input, stream_mode="messages"):
                # ── 检查停止信号 ──
                if stop_event.is_set():
                    yield _sse_event("stopped", {})
                    return

                if not event:
                    continue

                message, metadata = event
                node = metadata.get("langgraph_node", "")

                if node == "agent":
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tc in message.tool_calls:
                            tool_name = tc.get("name") or ""
                            tool_id = tc.get("id") or str(uuid.uuid4())
                            if not tool_name:
                                continue
                            tool_starts[tool_id] = time.time()
                            yield _sse_event("tool_call", {
                                "id": tool_id,
                                "tool": tool_name,
                                "args": tc.get("args", {}),
                            })
                        prev_text = ""

                    if hasattr(message, "content") and message.content:
                        text = message.content
                        if isinstance(text, str):
                            if text.startswith(prev_text):
                                delta = text[len(prev_text):]
                                prev_text = text
                                if delta:
                                    full_ai_response += delta  # ← 累积，不是覆盖
                                    has_any_output = True
                                    yield _sse_event("text", {"content": delta})
                            else:
                                # prev_text 被重置后第一段文本，或非累计流
                                prev_text = text
                                full_ai_response += text  # ← 累积
                                if text.strip():
                                    has_any_output = True
                                    yield _sse_event("text", {"content": text})

                elif node == "tools":
                    tool_name = message.name if hasattr(message, "name") else "unknown"
                    content = str(message.content) if hasattr(message, "content") else str(message)
                    tool_call_id = getattr(message, "tool_call_id", None) or ""
                    start = tool_starts.pop(tool_call_id, None)
                    duration = round(time.time() - start, 2) if start else None
                    status = "error" if any(
                        content.startswith(prefix) for prefix in ["[拒绝执行]", "[执行出错]", "[超时]", "计算出错", "❌"]
                    ) else "success"
                    prev_text = ""
                    yield _sse_event("tool_result", {
                        "id": tool_call_id,
                        "tool": tool_name,
                        "result": content[:500],
                        "duration": duration,
                        "status": status,
                    })

            # ── 后置：保存 AI 回复到记忆 ──
            if full_ai_response.strip():
                await pipeline.store_message(session_id, "assistant", full_ai_response)

            yield _sse_event("done", {})

        except asyncio.CancelledError:
            # 客户端断开连接
            yield _sse_event("stopped", {})
        except Exception as e:
            yield _sse_event("error", {"content": str(e)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ============================================================
# 停止生成
# ============================================================

@app.post("/stop/{session_id}")
async def stop_generation(session_id: str):
    """设置停止标记，通知 event_stream 立即终止。"""
    session = sessions.get(session_id)
    if session:
        session["stop_event"].set()
        return {"status": "stopped"}
    return JSONResponse({"status": "not_found"}, status_code=404)


# ============================================================
# 会话管理 API
# ============================================================

@app.get("/sessions")
async def list_sessions():
    """获取所有会话列表（不含消息内容）。"""
    return await repo.get_all_sessions()


@app.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """获取指定会话的全部消息。"""
    return await repo.get_messages(session_id)


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话及所有关联数据（消息 + 摘要）。"""
    await repo.delete_session(session_id)
    # 同时清理内存中的缓存
    sessions.pop(session_id, None)
    return {"status": "deleted"}


# ============================================================
# 工具函数
# ============================================================

def _sse_event(event: str, data: dict) -> str:
    """构造一条 SSE 事件字符串。"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _sse_gen(event: str, data: dict):
    """单事件 SSE 生成器（用于快速返回错误）。"""
    yield _sse_event(event, data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
