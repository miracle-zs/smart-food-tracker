import logging

import httpx

from app.config import settings


logger = logging.getLogger(__name__)

PUSHPLUS_ENDPOINT = "http://www.pushplus.plus/send"
SERVERCHAN_ENDPOINT = "https://sctapi.ftqq.com/{sendkey}.send"


class Notifier:
    def __init__(
        self,
        provider: str | None = None,
        webhook_url: str | None = None,
        pushplus_token: str | None = None,
        serverchan_key: str | None = None,
    ):
        self.provider = self._normalize_provider(provider or settings.notification_provider)
        self.webhook_url = webhook_url if webhook_url is not None else settings.notification_webhook_url
        self.pushplus_token = pushplus_token if pushplus_token is not None else settings.notification_pushplus_token
        self.serverchan_key = serverchan_key if serverchan_key is not None else settings.notification_serverchan_key

    def send(self, *, item, stage: str, days_left: int) -> None:
        message = self._build_message(item=item, stage=stage, days_left=days_left)

        if self.provider == "pushplus":
            if not self.pushplus_token:
                logger.info("Push Plus notification skipped because token is missing")
                return
            response = httpx.post(
                PUSHPLUS_ENDPOINT,
                json={
                    "token": self.pushplus_token,
                    "title": f"SmartFood Tracker 提醒：{item.name}",
                    "content": (
                        f"<p>{message}</p>"
                        f"<p>过期日期：{item.expiry_date.isoformat()}</p>"
                    ),
                    "template": "html",
                },
                timeout=10,
            )
            response.raise_for_status()
            return

        if self.provider == "serverchan":
            if not self.serverchan_key:
                logger.info("Server酱 notification skipped because sendkey is missing")
                return
            response = httpx.post(
                SERVERCHAN_ENDPOINT.format(sendkey=self.serverchan_key),
                data={
                    "title": f"SmartFood Tracker 提醒：{item.name}",
                    "desp": (
                        f"{message}\n\n"
                        f"过期日期：{item.expiry_date.isoformat()}"
                    ),
                },
                timeout=10,
            )
            response.raise_for_status()
            return

        if self.webhook_url:
            response = httpx.post(
                self.webhook_url,
                json={
                    "title": f"SmartFood Tracker 提醒：{item.name}",
                    "message": message,
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

    def _build_message(self, *, item, stage: str, days_left: int) -> str:
        return (
            f"{item.name} 存放于 {item.location}，距离过期还有 {days_left} 天，"
            f"当前节点 {stage}。"
        )

    def _normalize_provider(self, provider: str) -> str:
        normalized = provider.strip().lower()
        if normalized not in {"generic", "pushplus", "serverchan"}:
            return "generic"
        return normalized
