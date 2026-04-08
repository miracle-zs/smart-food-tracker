from datetime import date, datetime, timezone

from app.models.food_item import FoodItem
from app.services.notifier import Notifier


class FakeResponse:
    def raise_for_status(self):
        return None


def test_notifier_posts_to_webhook_when_configured(monkeypatch):
    captured = {}
    notifier = Notifier(webhook_url="https://example.com/webhook")
    item = FoodItem(
        id=1,
        name="鸡柳",
        location="冷冻室",
        entry_date=datetime(2026, 4, 8, tzinfo=timezone.utc),
        expiry_date=date(2026, 5, 8),
        status="active",
        needs_confirmation=False,
    )

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr("app.services.notifier.httpx.post", fake_post)

    notifier.send(item=item, stage="30d", days_left=30)

    assert captured["url"] == "https://example.com/webhook"
    assert "鸡柳" in captured["json"]["title"]
    assert captured["json"]["days_left"] == 30
