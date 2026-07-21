from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.savings.services.saving_plan import calculate_saving_plan, calculate_streak

TODAY = date(2026, 1, 1)


def _plan(**overrides):
    params = dict(
        target_amount=Decimal("1000"),
        start_date=TODAY + timedelta(days=100),
        trip_created_at=TODAY - timedelta(days=10),
        entry_amounts=[Decimal("50"), Decimal("30"), Decimal("20")],
        today=TODAY,
    )
    params.update(overrides)
    return calculate_saving_plan(**params)


class TestCalculateSavingPlan:
    def test_basic_projection_on_track(self):
        plan = _plan()

        assert plan.days_left == 100
        assert plan.saved == Decimal("100.00")
        assert plan.remaining == Decimal("900.00")
        assert plan.per_day == Decimal("9.00")
        assert plan.per_week == Decimal("63.00")
        assert plan.per_month == Decimal("270.00")
        assert plan.progress_pct == Decimal("10.00")
        assert plan.days_active == 10
        assert plan.actual_rate == Decimal("10.00")
        assert plan.projected_finish_days == 90
        assert plan.on_track is True

    def test_behind_schedule_is_not_on_track(self):
        plan = _plan(entry_amounts=[Decimal("1")], trip_created_at=TODAY - timedelta(days=90))
        # actual_rate = 1/90 ~= 0.01, remaining ~= 999 -> projected finish way beyond days_left
        assert plan.on_track is False

    def test_goal_already_reached(self):
        plan = _plan(entry_amounts=[Decimal("1200")])

        assert plan.remaining == Decimal("-200.00")
        assert plan.progress_pct == Decimal("100.00")
        assert plan.per_day == Decimal("0")
        assert plan.projected_finish_days == 0
        assert plan.on_track is True

    def test_no_savings_yet_is_undetermined(self):
        plan = _plan(entry_amounts=[])

        assert plan.saved == Decimal("0.00")
        assert plan.actual_rate == Decimal("0")
        assert plan.projected_finish_days is None
        assert plan.on_track is None
        # per_day is still a concrete target even with zero progress so far
        assert plan.per_day == Decimal("10.00")

    def test_start_date_in_the_past_does_not_divide_by_zero(self):
        plan = _plan(start_date=TODAY - timedelta(days=5))

        assert plan.days_left == -5
        assert plan.per_day == plan.remaining  # effective_days clamped to 1

    def test_per_day_rounds_up_to_the_cent(self):
        plan = _plan(
            target_amount=Decimal("100"),
            start_date=TODAY + timedelta(days=3),
            entry_amounts=[],
        )
        # remaining=100, effective_days=3 -> 33.333... rounds UP to 33.34
        assert plan.per_day == Decimal("33.34")

    def test_progress_never_exceeds_one_hundred_percent(self):
        plan = _plan(entry_amounts=[Decimal("5000")])
        assert plan.progress_pct == Decimal("100.00")

    def test_trip_created_today_still_has_at_least_one_active_day(self):
        plan = _plan(trip_created_at=TODAY)
        assert plan.days_active == 1

    def test_zero_target_amount_raises(self):
        with pytest.raises(ValueError):
            _plan(target_amount=Decimal("0"))

    def test_negative_target_amount_raises(self):
        with pytest.raises(ValueError):
            _plan(target_amount=Decimal("-10"))

    def test_as_dict_exposes_all_fields(self):
        plan = _plan()
        data = plan.as_dict()
        assert data["days_left"] == plan.days_left
        assert data["on_track"] == plan.on_track


class TestCalculateStreak:
    def test_no_entries_is_zero(self):
        assert calculate_streak([], today=TODAY) == 0

    def test_entry_today_only(self):
        assert calculate_streak([TODAY], today=TODAY) == 1

    def test_three_consecutive_days(self):
        dates = [TODAY, TODAY - timedelta(days=1), TODAY - timedelta(days=2)]
        assert calculate_streak(dates, today=TODAY) == 3

    def test_missing_today_resets_to_zero_even_with_history(self):
        dates = [TODAY - timedelta(days=1), TODAY - timedelta(days=2)]
        assert calculate_streak(dates, today=TODAY) == 0

    def test_gap_stops_the_count(self):
        dates = [TODAY, TODAY - timedelta(days=1), TODAY - timedelta(days=3)]
        assert calculate_streak(dates, today=TODAY) == 2
