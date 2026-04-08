from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.food_item import FoodItem
from app.services.notifier import Notifier


STAGE_BY_DAYS = {
    30: "30d",
    7: "7d",
    3: "3d",
}


class ReminderService:
    def __init__(self, notifier: Notifier | None = None):
        self.notifier = notifier or Notifier()

    def process_due_reminders(self, db: Session, today: date | None = None) -> int:
        current_date = today or date.today()
        items = db.scalars(select(FoodItem).where(FoodItem.status == "active")).all()
        sent_count = 0

        for item in items:
            days_left = (item.expiry_date - current_date).days
            stage = STAGE_BY_DAYS.get(days_left)
            if stage is None or item.last_notified_stage == stage:
                continue

            self.notifier.send(item=item, stage=stage, days_left=days_left)
            item.last_notified_stage = stage
            sent_count += 1

        db.commit()
        return sent_count
