from datetime import date, datetime, timezone

from app.config import settings
from app.models.food_item import FoodItem
from app.services.reminder_service import ReminderService


class RecordingNotifier:
    def __init__(self):
        self.sent = []

    def send(self, *, item, stage, days_left):
        self.sent.append(
            {
                "name": item.name,
                "stage": stage,
                "days_left": days_left,
            }
        )
        return True


def test_reminder_service_hits_active_thresholds_and_deduplicates(db_session):
    today = date(2026, 4, 8)
    db_session.add_all(
        [
            FoodItem(
                name="鸡柳",
                location="冷冻室",
                entry_date=datetime(2026, 4, 8, tzinfo=timezone.utc),
                expiry_date=date(2026, 5, 8),
                status="active",
                needs_confirmation=False,
            ),
            FoodItem(
                name="牛奶",
                location="冷藏室",
                entry_date=datetime(2026, 4, 8, tzinfo=timezone.utc),
                expiry_date=date(2026, 4, 15),
                status="active",
                needs_confirmation=False,
            ),
            FoodItem(
                name="酸奶",
                location="冷藏室",
                entry_date=datetime(2026, 4, 8, tzinfo=timezone.utc),
                expiry_date=date(2026, 4, 11),
                status="active",
                needs_confirmation=False,
                last_notified_stage="3d",
            ),
            FoodItem(
                name="薯片",
                location="零食柜",
                entry_date=datetime(2026, 4, 8, tzinfo=timezone.utc),
                expiry_date=date(2026, 4, 15),
                status="discarded",
                needs_confirmation=False,
            ),
        ]
    )
    db_session.commit()

    notifier = RecordingNotifier()
    service = ReminderService(notifier=notifier)

    reminders = service.process_due_reminders(db_session, today=today)

    assert reminders == 2
    assert notifier.sent == [
        {"name": "鸡柳", "stage": "30d", "days_left": 30},
        {"name": "牛奶", "stage": "7d", "days_left": 7},
    ]

    refreshed = db_session.query(FoodItem).order_by(FoodItem.name.asc()).all()
    stages = {item.name: item.last_notified_stage for item in refreshed}
    assert stages["鸡柳"] == "30d"
    assert stages["牛奶"] == "7d"
    assert stages["酸奶"] == "3d"
    assert stages["薯片"] is None


def test_reminder_service_uses_settings_defaults_for_provider(monkeypatch, db_session):
    today = date(2026, 4, 8)
    monkeypatch.setattr(settings, "notification_provider", "pushplus")
    monkeypatch.setattr(settings, "notification_pushplus_token", "pushplus-token")
    monkeypatch.setattr(settings, "notification_webhook_url", None)
    monkeypatch.setattr(settings, "notification_serverchan_key", None)

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return FakeResponse()

    monkeypatch.setattr("app.services.notifier.httpx.post", fake_post)

    db_session.add(
        FoodItem(
            name="鸡蛋",
            location="冷藏室",
            entry_date=datetime(2026, 4, 8, tzinfo=timezone.utc),
            expiry_date=date(2026, 5, 8),
            status="active",
            needs_confirmation=False,
        )
    )
    db_session.commit()

    reminders = ReminderService().process_due_reminders(db_session, today=today)

    assert reminders == 1
    assert captured["url"] == "https://www.pushplus.plus/send"
    assert captured["kwargs"]["json"]["token"] == "pushplus-token"

    refreshed = db_session.query(FoodItem).order_by(FoodItem.name.asc()).one()
    assert refreshed.last_notified_stage == "30d"


def test_reminder_service_does_not_mark_stage_when_notification_credentials_missing(monkeypatch, db_session):
    today = date(2026, 4, 8)
    monkeypatch.setattr(settings, "notification_provider", "pushplus")
    monkeypatch.setattr(settings, "notification_pushplus_token", None)
    monkeypatch.setattr(settings, "notification_webhook_url", None)
    monkeypatch.setattr(settings, "notification_serverchan_key", None)

    db_session.add(
        FoodItem(
            name="面包",
            location="餐桌",
            entry_date=datetime(2026, 4, 8, tzinfo=timezone.utc),
            expiry_date=date(2026, 4, 11),
            status="active",
            needs_confirmation=False,
        )
    )
    db_session.commit()

    reminders = ReminderService().process_due_reminders(db_session, today=today)

    assert reminders == 0
    refreshed = db_session.query(FoodItem).order_by(FoodItem.name.asc()).one()
    assert refreshed.last_notified_stage is None


def test_reminder_service_does_not_mark_stage_for_unsupported_provider(monkeypatch, db_session):
    today = date(2026, 4, 8)
    monkeypatch.setattr(settings, "notification_provider", "pushpluss")
    monkeypatch.setattr(settings, "notification_webhook_url", "https://example.com/webhook")
    monkeypatch.setattr(settings, "notification_pushplus_token", "pushplus-token")
    monkeypatch.setattr(settings, "notification_serverchan_key", "SCT-token")

    def fake_post(*args, **kwargs):
        raise AssertionError("httpx.post should not be called for unsupported providers")

    monkeypatch.setattr("app.services.notifier.httpx.post", fake_post)

    db_session.add(
        FoodItem(
            name="苹果",
            location="果盘",
            entry_date=datetime(2026, 4, 8, tzinfo=timezone.utc),
            expiry_date=date(2026, 5, 8),
            status="active",
            needs_confirmation=False,
        )
    )
    db_session.commit()

    reminders = ReminderService().process_due_reminders(db_session, today=today)

    assert reminders == 0
    refreshed = db_session.query(FoodItem).order_by(FoodItem.name.asc()).one()
    assert refreshed.last_notified_stage is None


def test_reminder_service_advances_stage_in_mock_generic_mode(monkeypatch, db_session):
    today = date(2026, 4, 8)
    monkeypatch.setattr(settings, "notification_provider", "generic")
    monkeypatch.setattr(settings, "notification_webhook_url", None)
    monkeypatch.setattr(settings, "notification_pushplus_token", None)
    monkeypatch.setattr(settings, "notification_serverchan_key", None)

    db_session.add(
        FoodItem(
            name="香蕉",
            location="餐桌",
            entry_date=datetime(2026, 4, 8, tzinfo=timezone.utc),
            expiry_date=date(2026, 5, 8),
            status="active",
            needs_confirmation=False,
        )
    )
    db_session.commit()

    reminders = ReminderService().process_due_reminders(db_session, today=today)

    assert reminders == 1
    refreshed = db_session.query(FoodItem).order_by(FoodItem.name.asc()).one()
    assert refreshed.last_notified_stage == "30d"
