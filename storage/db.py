"""
持久化层 —— SQLite 数据库连接管理。

使用 SQLAlchemy 2.0 async + aiosqlite，零配置。
"""

import os
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.settings import settings


class Database:
    """数据库连接管理器。"""

    def __init__(self, url: str = None):
        # sqlite:///agent.db → sqlite+aiosqlite:///agent.db
        raw = url or settings.DATABASE_URL
        if raw.startswith("sqlite:///"):
            # 确保路径是绝对路径，基于项目根目录
            db_path = raw[len("sqlite:///"):]
            if not os.path.isabs(db_path):
                # 以项目目录为基准
                base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                db_path = os.path.join(base, db_path)
                raw = f"sqlite:///{db_path}"
            async_url = raw.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        else:
            async_url = raw
        self._engine = create_async_engine(async_url, echo=False)

        # SQLite 默认关闭外键约束 —— 必须打开 CASCADE 才生效
        @event.listens_for(self._engine.sync_engine, "connect")
        def _enable_foreign_keys(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

    @property
    def engine(self):
        return self._engine

    def session(self) -> AsyncSession:
        """获取一个异步数据库会话。"""
        return self._session_factory()

    async def create_tables(self, base):
        """创建所有表（如果不存在）。"""
        async with self._engine.begin() as conn:
            await conn.run_sync(base.metadata.create_all)

    async def disconnect(self):
        """关闭连接池。"""
        await self._engine.dispose()


# 全局单例 —— 其他地方 import db 即可使用
from storage.models import Base

db = Database()

async def init_db():
    """应用启动时调用，初始化表结构。"""
    await db.create_tables(Base)
