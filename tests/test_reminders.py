from datetime import date, datetime, timezone

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
