from datetime import date, datetime, timezone

from app.models.food_item import FoodItem
from app.services.notifier import Notifier


class FakeResponse:
    def raise_for_status(self):
        return None


def test_notifier_posts_to_webhook_when_configured(monkeypatch):
    captured = {}
    notifier = Notifier(provider="generic", webhook_url="https://example.com/webhook")
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


def test_notifier_posts_pushplus_payload(monkeypatch):
    captured = {}
    notifier = Notifier(provider="pushplus", pushplus_token="pushplus-token")
    item = FoodItem(
        id=2,
        name="牛奶",
        location="冷藏室",
        entry_date=datetime(2026, 4, 8, tzinfo=timezone.utc),
        expiry_date=date(2026, 4, 15),
        status="active",
        needs_confirmation=False,
    )

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return FakeResponse()

    monkeypatch.setattr("app.services.notifier.httpx.post", fake_post)

    notifier.send(item=item, stage="7d", days_left=7)

    assert captured["url"] == "http://www.pushplus.plus/send"
    assert captured["kwargs"]["json"] == {
        "token": "pushplus-token",
        "title": "SmartFood Tracker 提醒：牛奶",
        "content": (
            "<p>牛奶 存放于 冷藏室，距离过期还有 7 天，当前节点 7d。</p>"
            "<p>过期日期：2026-04-15</p>"
        ),
        "template": "html",
    }


def test_notifier_posts_serverchan_payload(monkeypatch):
    captured = {}
    notifier = Notifier(provider="serverchan", serverchan_key="SCT-token")
    item = FoodItem(
        id=3,
        name="酸奶",
        location="冷藏室",
        entry_date=datetime(2026, 4, 8, tzinfo=timezone.utc),
        expiry_date=date(2026, 4, 11),
        status="active",
        needs_confirmation=False,
    )

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return FakeResponse()

    monkeypatch.setattr("app.services.notifier.httpx.post", fake_post)

    notifier.send(item=item, stage="3d", days_left=3)

    assert captured["url"] == "https://sctapi.ftqq.com/SCT-token.send"
    assert captured["kwargs"]["data"] == {
        "title": "SmartFood Tracker 提醒：酸奶",
        "desp": (
            "酸奶 存放于 冷藏室，距离过期还有 3 天，当前节点 3d。\n\n"
            "过期日期：2026-04-11"
        ),
    }
