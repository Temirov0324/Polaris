from datetime import timedelta
from decimal import Decimal

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q, Sum
from django.utils import timezone

from apps.destinations.models import PriceReference
from apps.savings.services.saving_plan import calculate_streak, get_saving_plan
from apps.telegram_bot.services import send_message as send_telegram_message
from apps.trips.models import Trip
from apps.trips.services.budget_calculator import estimate_trip_budget

PRICE_DROP_THRESHOLD = Decimal("0.05")  # 5%+ pasayish bo'lsagina xabar beramiz


def _notify(user, subject, message):
    """Telegram (much higher open rates for this user base) if the account
    is linked, otherwise email. Both are best-effort — a delivery failure
    here must never fail the calling task."""
    if user.telegram_chat_id:
        send_telegram_message(user.telegram_chat_id, f"{subject}\n\n{message}")
        return
    if user.email:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )


def _active_trips_with_target():
    return (
        Trip.objects.filter(
            status__in=[Trip.Status.PLANNING, Trip.Status.SAVING],
            target_amount__isnull=False,
        )
        .exclude(Q(user__email="") & Q(user__telegram_chat_id__isnull=True))
        .select_related("user", "destination")
    )


@shared_task
def daily_saving_reminder():
    """20:00 (Asia/Tashkent) — "Bugun $X jamg'arishni unutmang. {Yo'nalish}gacha {N} kun."."""
    sent = 0
    for trip in _active_trips_with_target().filter(user__notify_daily=True):
        plan = get_saving_plan(trip)
        if plan.days_left <= 0 or plan.remaining <= 0:
            continue
        _notify(
            trip.user,
            "PolarisAI — bugungi jamg'arish eslatmasi",
            (
                f"Salom {trip.user.full_name}!\n\n"
                f"Bugun ${plan.per_day} jamg'arishni unutmang. "
                f"{trip.destination.city_uz}gacha {plan.days_left} kun qoldi.\n\n— PolarisAI"
            ),
        )
        sent += 1
    return sent


@shared_task
def check_price_drops():
    """09:00 — narx ma'lumotlari (PriceReference) yangilanib, taxminiy
    byudjet trip yaratilgan paytdagidan kamida 5% pastga tushgan bo'lsa,
    foydalanuvchiga xabar beramiz va trip'ning bazaviy byudjetini
    yangilaymiz (keyingi solishtiruv shundan boshlansin)."""
    sent = 0
    trips = (
        Trip.objects.filter(status__in=[Trip.Status.PLANNING, Trip.Status.SAVING], user__notify_price_drop=True)
        .exclude(Q(user__email="") & Q(user__telegram_chat_id__isnull=True))
        .select_related("user", "destination__country")
    )
    for trip in trips:
        try:
            result = estimate_trip_budget(
                destination=trip.destination,
                start_date=trip.start_date,
                duration_days=trip.duration_days,
                travelers_count=trip.travelers_count,
                style=trip.style,
            )
        except PriceReference.DoesNotExist:
            continue

        old_min = trip.budget_min
        if old_min <= 0:
            continue

        drop_pct = (old_min - result.budget_min) / old_min
        if drop_pct < PRICE_DROP_THRESHOLD:
            continue

        _notify(
            trip.user,
            "PolarisAI — narx pasaydi!",
            (
                f"Salom {trip.user.full_name}!\n\n"
                f"{trip.destination.city_uz} yo'nalishi uchun taxminiy byudjet pasaydi: "
                f"${old_min} -> ${result.budget_min} (-{int(drop_pct * 100)}%).\n\n— PolarisAI"
            ),
        )
        trip.budget_min = result.budget_min
        trip.budget_max = result.budget_max
        trip.save(update_fields=["budget_min", "budget_max"])
        sent += 1
    return sent


@shared_task
def weekly_progress():
    """Yakshanba 10:00 — "Bu hafta $X yig'dingiz. Maqsadning Y%i bajarildi."."""
    sent = 0
    week_ago = timezone.localdate() - timedelta(days=7)
    for trip in _active_trips_with_target().filter(user__notify_weekly=True):
        plan = get_saving_plan(trip)
        week_total = trip.saving_entries.filter(date__gte=week_ago).aggregate(total=Sum("amount"))["total"] or 0
        _notify(
            trip.user,
            "PolarisAI — haftalik hisobot",
            (
                f"Salom {trip.user.full_name}!\n\n"
                f"Bu hafta ${week_total} yig'dingiz. Maqsadning {plan.progress_pct}%i bajarildi.\n\n— PolarisAI"
            ),
        )
        sent += 1
    return sent


@shared_task
def streak_warning():
    """21:30 — faqat streak > 3 va bugun hali yozuv qo'shilmagan bo'lsa."""
    sent = 0
    today = timezone.localdate()
    for trip in _active_trips_with_target().filter(user__notify_streak=True):
        entry_dates = set(trip.saving_entries.values_list("date", flat=True))
        if today in entry_dates:
            continue

        streak_through_yesterday = calculate_streak(entry_dates, today=today - timedelta(days=1))
        if streak_through_yesterday <= 3:
            continue

        _notify(
            trip.user,
            "PolarisAI — streak'ingiz xavf ostida!",
            (
                f"Salom {trip.user.full_name}!\n\n"
                f"{streak_through_yesterday} kunlik jamg'arish streak'ingizni yo'qotmang — "
                f"bugun hali yozuv qo'shmadingiz.\n\n— PolarisAI"
            ),
        )
        sent += 1
    return sent
