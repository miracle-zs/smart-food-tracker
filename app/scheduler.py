from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.api.routes.items import get_db
from app.config import settings
from app.services.reminder_service import ReminderService


scheduler = BackgroundScheduler()
reminder_service = ReminderService()


def run_daily_reminder_scan() -> int:
    db = next(get_db())
    try:
        return reminder_service.process_due_reminders(db)
    finally:
        db.close()


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(
        run_daily_reminder_scan,
        trigger=CronTrigger(hour=settings.reminder_hour, minute=0),
        id="daily-reminder-scan",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
