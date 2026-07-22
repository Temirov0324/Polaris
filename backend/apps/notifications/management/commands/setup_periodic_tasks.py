from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask

TIMEZONE = "Asia/Tashkent"

SCHEDULES = {
    "daily-saving-reminder": {
        "task": "apps.notifications.tasks.daily_saving_reminder",
        "cron": dict(minute="0", hour="20", day_of_week="*", day_of_month="*", month_of_year="*"),
    },
    "weekly-progress": {
        "task": "apps.notifications.tasks.weekly_progress",
        "cron": dict(minute="0", hour="10", day_of_week="0", day_of_month="*", month_of_year="*"),  # Yakshanba
    },
    "streak-warning": {
        "task": "apps.notifications.tasks.streak_warning",
        "cron": dict(minute="30", hour="21", day_of_week="*", day_of_month="*", month_of_year="*"),
    },
    "price-drop-check": {
        "task": "apps.notifications.tasks.check_price_drops",
        "cron": dict(minute="0", hour="9", day_of_week="*", day_of_month="*", month_of_year="*"),
    },
}


class Command(BaseCommand):
    help = "Registers the daily/weekly/streak Celery Beat periodic tasks (idempotent, Asia/Tashkent timezone)."

    def handle(self, *args, **options):
        for name, config in SCHEDULES.items():
            schedule, _ = CrontabSchedule.objects.get_or_create(timezone=TIMEZONE, **config["cron"])
            PeriodicTask.objects.update_or_create(
                name=name,
                defaults={"task": config["task"], "crontab": schedule, "enabled": True},
            )

        self.stdout.write(self.style.SUCCESS(f"{len(SCHEDULES)} ta rejalashtirilgan vazifa sozlandi."))
