import os
from pathlib import Path

from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "SmartFood Tracker")
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'smartfood.db'}")
    reminder_hour: int = int(os.getenv("REMINDER_HOUR", "10"))
    llm_api_key: str | None = os.getenv("LLM_API_KEY")
    llm_base_url: str | None = os.getenv("LLM_BASE_URL")
    llm_model: str | None = os.getenv("LLM_MODEL")
    notification_provider: str = os.getenv("NOTIFICATION_PROVIDER", "generic")
    notification_webhook_url: str | None = os.getenv("NOTIFICATION_WEBHOOK_URL")
    notification_pushplus_token: str | None = os.getenv("NOTIFICATION_PUSHPLUS_TOKEN")
    notification_serverchan_key: str | None = os.getenv("NOTIFICATION_SERVERCHAN_KEY")


settings = Settings()
