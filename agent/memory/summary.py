"""
摘要记忆 (Summary Memory) —— 完整实现版。

功能：
  1. 全量消息写入 SQLite（通过 storage/repo.py）
  2. 每 N 轮自动生成增量摘要
  3. get_context() 返回最新摘要
  4. 兼容 pipeline 的 collect() 协议
"""

from typing import Any, Optional

from agent.memory.base import BaseMemory
from config.settings import settings
from storage import repo


# 默认摘要 prompt（可自定义）
DEFAULT_SUMMARY_PROMPT = """你是一个对话摘要助手。你的任务是阅读已有的摘要和最新的对话记录，生成更新后的摘要。

要求：
- 保留关键信息：用户意图、重要决策、任务状态、偏好设置、已执行的结果
- 保持简洁但完整，确保另一个 AI 可以仅靠摘要继续对话而不丢失上下文
- 只输出摘要文本，不要多余的解释

之前的摘要：
{previous_summary}

新增的对话记录：
{new_messages}

更新后的摘要：
"""


class SummaryMemory(BaseMemory):
    """摘要记忆。"""

    def __init__(
        self,
        summary_llm=None,
        summary_interval: int = 5,
        priority: int = 55,
        max_summary_tokens: int = 1000,
        summary_prompt: str = DEFAULT_SUMMARY_PROMPT,
    ):
        self.summary_llm = summary_llm
        self.summary_interval = summary_interval
        self.priority = priority
        self.max_summary_tokens = max_summary_tokens
        self.summary_prompt = summary_prompt

    @property
    def name(self) -> str:
        return "summary"

    # ── BaseMemory 接口 ──

    async def add(self, session_id: str, message: Any) -> None:
        """记录一条消息到数据库，并在达到轮数阈值时触发摘要。"""
        if isinstance(message, dict):
            role = message.get("role", "unknown")
            content = message.get("content", "")
        else:
            role = getattr(message, "role", "unknown")
            content = getattr(message, "content", str(message))

        # 跳过工具消息（不写入 DB，也不计入轮数）
        if role == "tool":
            return

        # 1. 先确保 session 存在（外键约束要求 sessions 行必须先有）
        await repo.get_or_create_session(session_id)
        if role == "user":
            await repo.update_session_title(session_id, content)

        # 2. 写入消息
        await repo.save_message(session_id, role, content)

        # 3. 判断是否需要触发摘要（按 user 消息轮数）
        if role == "user":
            user_turns = await repo.count_user_turns(session_id)
            if user_turns > 0 and user_turns % self.summary_interval == 0:
                await self._generate_summary(session_id)

    async def get_context(self, session_id: str, query: str) -> Optional[str]:
        """从数据库读取最新摘要。"""
        latest = await repo.get_latest_summary(session_id)
        if latest and latest["summary"]:
            return f"[对话摘要]\n{latest['summary']}"
        return None

    async def clear(self, session_id: str) -> None:
        """删除该会话的全部数据（CASCADE 会处理 messages + summaries）。"""
        await repo.delete_session(session_id)

    # ── 摘要生成 ──

    async def _generate_summary(self, session_id: str) -> str:
        """触发增量摘要生成并存入数据库。"""
        # 1. 取旧摘要
        latest = await repo.get_latest_summary(session_id)
        prev_summary = latest["summary"] if latest else ""
        last_msg_id = latest["last_msg_id"] if latest else 0

        # 2. 取新消息（last_msg_id 之后的 user 和 assistant 消息）
        all_msgs = await repo.get_messages(session_id)
        new_msgs = [m for m in all_msgs if m["id"] > last_msg_id and m["role"] in ("user", "assistant")]
        if not new_msgs:
            return prev_summary  # 没有新消息，直接返回旧摘要

        new_text = "\n".join(
            f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content']}"
            for m in new_msgs
        )

        # 3. 调用 LLM
        if self.summary_llm:
            prompt = self.summary_prompt.format(
                previous_summary=prev_summary or "(尚无摘要)",
                new_messages=new_text,
            )
            try:
                response = await self.summary_llm.ainvoke(prompt)
                new_summary = response.content if hasattr(response, "content") else str(response)
            except Exception as e:
                print(f"[summary] LLM 调用失败: {e}")
                return prev_summary
        else:
            # 没有 summary_llm 时的 fallback：拼接新旧 + 截断
            combined = prev_summary + "\n" + new_text if prev_summary else new_text
            new_summary = combined[:self.max_summary_tokens * 4]

        # 4. 截断保护
        if len(new_summary) > self.max_summary_tokens * 4:
            new_summary = new_summary[:self.max_summary_tokens * 4] + "…"

        # 5. 写入数据库
        new_version = (latest["version"] if latest else 0) + 1
        latest_msg_id = new_msgs[-1]["id"]
        await repo.save_summary(session_id, new_summary, latest_msg_id, new_version)

        return new_summary

    # ── ContextStrategy 兼容 ──

    async def collect(self, session_id: str, query: str) -> Optional[dict[str, Any]]:
        """供 pipeline 编排使用的策略片段。"""
        content = await self.get_context(session_id, query)
        if not content:
            return None
        return {
            "priority": self.priority,
            "content": content,
            "tokens": len(content) // 4,
        }
