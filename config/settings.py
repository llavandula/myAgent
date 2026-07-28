"""
全局配置，从 .env 读取，集中管理所有参数。
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Agent 配置"""

    # ---- 模型 ----
    MODEL_PROVIDER: str = os.getenv("MODEL_PROVIDER", "deepseek")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "deepseek-chat")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))

    # ---- API ----
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "")

    @property
    def api_key(self) -> str:
        """根据 provider 返回对应的 API Key"""
        if self.MODEL_PROVIDER == "openai":
            return self.OPENAI_API_KEY
        return self.DEEPSEEK_API_KEY

    @property
    def base_url(self) -> str:
        """根据 provider 返回对应的 Base URL"""
        if self.MODEL_PROVIDER == "openai":
            return self.OPENAI_BASE_URL or "https://api.openai.com/v1"
        return self.DEEPSEEK_BASE_URL


settings = Settings()
