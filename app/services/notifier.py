import logging

import httpx

from app.config import settings


logger = logging.getLogger(__name__)


class Notifier:
    def __init__(self, webhook_url: str | None = None):
        self.webhook_url = webhook_url if webhook_url is not None else settings.notification_webhook_url

    def send(self, *, item, stage: str, days_left: int) -> None:
        if self.webhook_url:
            response = httpx.post(
                self.webhook_url,
                json={
                    "title": f"SmartFood Tracker 提醒：{item.name}",
                    "message": (
                        f"{item.name} 存放于 {item.location}，距离过期还有 {days_left} 天，"
                        f"当前节点 {stage}。"
                    ),
                    "item_name": item.name,
                    "location": item.location,
                    "expiry_date": item.expiry_date.isoformat(),
                    "days_left": days_left,
                    "stage": stage,
                },
                timeout=10,
            )
            response.raise_for_status()
            return

        logger.info(
            "Reminder sent",
            extra={
                "item": item.name,
                "location": item.location,
                "stage": stage,
                "days_left": days_left,
            },
        )
