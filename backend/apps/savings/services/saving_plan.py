"""Pure saving-plan math (section 5 of TEXNIK_TOPSHIRIQ.md).

`calculate_saving_plan` and `calculate_streak` take plain dates/Decimals and
return plain dataclasses/ints — no ORM access, fully unit-testable.
`get_saving_plan` is the thin DB-touching wrapper the /trips/{id}/plan/ view
calls.
"""
import math
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Optional

TWO_PLACES = Decimal("0.01")


def _q(value: Decimal) -> Decimal:
    return Decimal(value).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _ceil_to_cent(value: Decimal) -> Decimal:
    return Decimal(math.ceil(value * 100)) / 100


@dataclass(frozen=True)
class SavingPlan:
    days_left: int
    per_day: Decimal
    per_week: Decimal
    per_month: Decimal
    saved: Decimal
    remaining: Decimal
    progress_pct: Decimal
    days_active: int
    actual_rate: Decimal
    projected_finish_days: Optional[int]
    on_track: Optional[bool]

    def as_dict(self):
        return asdict(self)


def calculate_saving_plan(
    *,
    target_amount: Decimal,
    start_date: date,
    trip_created_at: date,
    entry_amounts: Iterable[Decimal],
    today: Optional[date] = None,
) -> SavingPlan:
    if target_amount <= 0:
        raise ValueError("target_amount 0 dan katta bo'lishi kerak")

    today = today or date.today()
    target_amount = Decimal(target_amount)

    days_left = (start_date - today).days
    effective_days = max(days_left, 1)  # sayohat sanasi o'tib ketgan bo'lsa ham 0'ga bo'linmasin

    saved = sum((Decimal(a) for a in entry_amounts), Decimal("0"))
    remaining = target_amount - saved

    per_day = _ceil_to_cent(remaining / effective_days) if remaining > 0 else Decimal("0")
    per_week = _q(per_day * 7)
    per_month = _q(per_day * 30)

    progress_pct = _q(min(saved, target_amount) / target_amount * 100) if target_amount > 0 else Decimal("0")

    days_active = (today - trip_created_at).days or 1
    actual_rate = _q(saved / days_active) if days_active > 0 else Decimal("0")

    projected_finish_days = None
    on_track = None
    if remaining <= 0:
        projected_finish_days = 0
        on_track = True
    elif actual_rate > 0:
        projected_finish_days = math.ceil(remaining / actual_rate)
        on_track = projected_finish_days <= days_left

    return SavingPlan(
        days_left=days_left,
        per_day=per_day,
        per_week=per_week,
        per_month=per_month,
        saved=_q(saved),
        remaining=_q(remaining),
        progress_pct=progress_pct,
        days_active=days_active,
        actual_rate=actual_rate,
        projected_finish_days=projected_finish_days,
        on_track=on_track,
    )


def calculate_streak(entry_dates: Iterable[date], today: Optional[date] = None) -> int:
    """Consecutive days (counting back from today) that have a SavingEntry.
    Missing today, or any single gap, resets the streak to 0."""
    today = today or date.today()
    dates = set(entry_dates)

    streak = 0
    day = today
    while day in dates:
        streak += 1
        day -= timedelta(days=1)
    return streak


def get_saving_plan(trip) -> SavingPlan:
    from django.utils import timezone

    entry_amounts = trip.saving_entries.values_list("amount", flat=True)
    return calculate_saving_plan(
        target_amount=trip.target_amount,
        start_date=trip.start_date,
        trip_created_at=timezone.localtime(trip.created_at).date(),
        entry_amounts=entry_amounts,
        today=timezone.localdate(),
    )
