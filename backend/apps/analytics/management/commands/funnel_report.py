from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from apps.analytics.models import AnalyticsEvent

FUNNEL = [
    "landing_viewed",
    "register_started",
    "register_verified",
    "wizard_step_viewed",
    "trip_created",
    "saving_entry_added",
    "chat_message_sent",
    "member_invited",
]


class Command(BaseCommand):
    help = "Prints event counts (all-time and last 7 days) for the core signup/activation funnel."

    def handle(self, *args, **options):
        since = timezone.now() - timedelta(days=7)
        all_qs = AnalyticsEvent.objects.filter(name__in=FUNNEL)
        recent_qs = all_qs.filter(created_at__gte=since)
        counts_all = dict(all_qs.values("name").annotate(c=Count("id")).values_list("name", "c"))
        counts_7d = dict(recent_qs.values("name").annotate(c=Count("id")).values_list("name", "c"))

        self.stdout.write(self.style.SUCCESS("PolarisAI — funnel hisoboti"))
        self.stdout.write(f"{'Hodisa':<24}{'Jami':>10}{'So‘nggi 7 kun':>16}")
        self.stdout.write("-" * 50)
        for name in FUNNEL:
            self.stdout.write(f"{name:<24}{counts_all.get(name, 0):>10}{counts_7d.get(name, 0):>16}")

        reg_started = counts_all.get("register_started", 0)
        reg_verified = counts_all.get("register_verified", 0)
        trip_created = counts_all.get("trip_created", 0)
        if reg_started:
            self.stdout.write("")
            rate = reg_verified / reg_started
            self.stdout.write(f"Ro'yxatdan o'tish -> tasdiqlash: {reg_verified}/{reg_started} ({rate:.0%})")
        if reg_verified:
            rate = trip_created / reg_verified
            self.stdout.write(f"Tasdiqlash -> birinchi sayohat: {trip_created}/{reg_verified} ({rate:.0%})")
