"""
数据访问层 —— 封装对 sessions / messages / summaries 的 CRUD 操作。
供 SummaryMemory 和 server.py 路由使用。
"""

from typing import Optional
from sqlalchemy import select, delete
from storage.db import db
from storage.models import SessionRecord, MessageRecord, SummaryRecord


# ============================================================
# Session
# ============================================================

async def get_or_create_session(session_id: str, title: str = "") -> SessionRecord:
    """获取或创建会话记录。"""
    async with db.session() as s:
        row = await s.get(SessionRecord, session_id)
        if row:
            return row
        row = SessionRecord(id=session_id, title=title[:200])
        s.add(row)
        await s.commit()
        return row


async def get_all_sessions() -> list[dict]:
    """按更新时间降序返回所有会话（id, title, created_at, updated_at, msg_count）。"""
    async with db.session() as s:
        from sqlalchemy import func as f
        subq = (
            select(
                MessageRecord.session_id,
                f.count(MessageRecord.id).label("cnt")
            )
            .group_by(MessageRecord.session_id)
            .subquery()
        )
        stmt = (
            select(SessionRecord, subq.c.cnt)
            .outerjoin(subq, SessionRecord.id == subq.c.session_id)
            .order_by(SessionRecord.updated_at.desc())
        )
        rows = await s.execute(stmt)
        results = []
        for row_obj, cnt in rows:
            results.append({
                "id": row_obj.id,
                "title": row_obj.title or "新对话",
                "created_at": row_obj.created_at.isoformat() if row_obj.created_at else "",
                "updated_at": row_obj.updated_at.isoformat() if row_obj.updated_at else "",
                "msg_count": cnt or 0,
            })
        return results


async def update_session_title(session_id: str, title: str):
    """更新会话标题（取首条用户消息截断）。"""
    async with db.session() as s:
        row = await s.get(SessionRecord, session_id)
        if row and not row.title:
            row.title = title[:200]
            await s.commit()


async def delete_session(session_id: str):
    """删除会话及其全部消息和摘要。"""
    async with db.session() as s:
        # 先显式删除关联数据（PRAGMA foreign_keys=ON 后 CASCADE 也会生效，双重保障）
        await s.execute(delete(MessageRecord).where(MessageRecord.session_id == session_id))
        await s.execute(delete(SummaryRecord).where(SummaryRecord.session_id == session_id))
        row = await s.get(SessionRecord, session_id)
        if row:
            await s.delete(row)
        await s.commit()


# ============================================================
# Message
# ============================================================

async def save_message(session_id: str, role: str, content: str) -> int:
    """写入一条消息，返回自增 ID。"""
    async with db.session() as s:
        msg = MessageRecord(session_id=session_id, role=role, content=content)
        s.add(msg)
        await s.commit()
        await s.refresh(msg)
        return msg.id


async def get_messages(session_id: str) -> list[dict]:
    """按顺序返回会话的全部消息。"""
    async with db.session() as s:
        stmt = (
            select(MessageRecord)
            .where(MessageRecord.session_id == session_id)
            .order_by(MessageRecord.id)
        )
        rows = await s.execute(stmt)
        return [
            {"id": r.id, "role": r.role, "content": r.content, "created_at": r.created_at.isoformat() if r.created_at else ""}
            for r in rows.scalars()
        ]


async def count_messages(session_id: str) -> int:
    """统计会话消息数。"""
    async with db.session() as s:
        from sqlalchemy import func as f
        stmt = select(f.count(MessageRecord.id)).where(MessageRecord.session_id == session_id)
        row = await s.execute(stmt)
        return row.scalar() or 0


async def count_user_turns(session_id: str) -> int:
    """统计 user 消息数量（用于触发摘要）。"""
    async with db.session() as s:
        from sqlalchemy import func as f
        stmt = (
            select(f.count(MessageRecord.id))
            .where(MessageRecord.session_id == session_id, MessageRecord.role == "user")
        )
        row = await s.execute(stmt)
        return row.scalar() or 0


# ============================================================
# Summary
# ============================================================

async def get_latest_summary(session_id: str) -> Optional[dict]:
    """获取最新版摘要。"""
    async with db.session() as s:
        stmt = (
            select(SummaryRecord)
            .where(SummaryRecord.session_id == session_id)
            .order_by(SummaryRecord.version.desc())
            .limit(1)
        )
        row = await s.execute(stmt)
        r = row.scalar_one_or_none()
        if r:
            return {
                "id": r.id,
                "summary": r.summary,
                "version": r.version,
                "last_msg_id": r.last_msg_id,
                "updated_at": r.updated_at.isoformat() if r.updated_at else "",
            }
        return None


async def save_summary(session_id: str, summary: str, last_msg_id: int, version: int):
    """写入一条新版本摘要。"""
    async with db.session() as s:
        rec = SummaryRecord(
            session_id=session_id,
            summary=summary,
            version=version,
            last_msg_id=last_msg_id,
        )
        s.add(rec)
        await s.commit()
