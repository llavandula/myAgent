"""
数据库 ORM 模型 —— SQLAlchemy 2.0 async 声明式映射。

三张表：
  sessions   — 会话元信息（标题、创建/更新时间）
  messages   — 全量消息记录
  summaries  — 摘要记录
"""

import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class SessionRecord(Base):
    """会话表。"""
    __tablename__ = "sessions"

    id = Column(String(64), primary_key=True)                     # session_id (UUID)
    title = Column(String(200), default="", server_default="")    # 会话标题（首条消息截取）
    created_at = Column(DateTime, default=datetime.datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, server_default=func.now(), onupdate=datetime.datetime.utcnow)


class MessageRecord(Base):
    """消息记录表。"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(16), nullable=False)                     # user / assistant / tool
    content = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, server_default=func.now())


class SummaryRecord(Base):
    """摘要记录表。"""
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    summary = Column(Text, nullable=False, default="")
    version = Column(Integer, default=0, server_default="0")      # 版本号，每次增量+1
    last_msg_id = Column(Integer, default=0, server_default="0")  # 被汇总的最后一条 message.id
    created_at = Column(DateTime, default=datetime.datetime.utcnow, server_default=func.now())
