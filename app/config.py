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
    notification_webhook_url: str | None = os.getenv("NOTIFICATION_WEBHOOK_URL")


settings = Settings()
