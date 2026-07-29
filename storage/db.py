"""
持久化层 —— 数据库连接管理。

支持后端：
  - SQLite（本地开发，零配置）
  - PostgreSQL（生产环境）
"""


class Database:
    """数据库连接管理器。"""

    def __init__(self, url: str = "sqlite:///agent.db"):
        self.url = url
        self._engine = None

    async def connect(self):
        """初始化连接池。"""
        ...

    async def disconnect(self):
        """关闭连接。"""
        ...

    @property
    def engine(self):
        """获取 SQLAlchemy Engine。"""
        return self._engine
