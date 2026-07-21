from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core import mail

from apps.destinations.models import Country, Destination
from apps.notifications.tasks import daily_saving_reminder, streak_warning, weekly_progress
from apps.savings.models import SavingEntry
from apps.trips.models import Trip
from apps.users.models import User


@pytest.fixture
def destination(db):
    country = Country.objects.create(
        name_uz="Gruziya", name_en="Georgia", code="GE", visa_type="free", visa_cost_usd=0
    )
    return Destination.objects.create(country=country, city_uz="Tbilisi", city_en="Tbilisi")


def _make_user(phone, email="", **overrides):
    return User.objects.create_user(
        phone=phone, full_name="Sayohatchi", password="testpass123", email=email, **overrides
    )


def _make_trip(user, destination, target_amount=Decimal("500"), start_offset_days=30):
    return Trip.objects.create(
        user=user,
        destination=destination,
        start_date=date.today() + timedelta(days=start_offset_days),
        duration_days=5,
        budget_min=Decimal("400"),
        budget_max=Decimal("600"),
        target_amount=target_amount,
        status=Trip.Status.SAVING,
    )


@pytest.mark.django_db
class TestDailySavingReminder:
    def test_sends_email_to_eligible_user(self, destination):
        user = _make_user("+998900000001", email="a@example.com", notify_daily=True)
        _make_trip(user, destination)

        sent = daily_saving_reminder()

        assert sent == 1
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["a@example.com"]

    def test_skips_user_with_notifications_disabled(self, destination):
        user = _make_user("+998900000002", email="b@example.com", notify_daily=False)
        _make_trip(user, destination)

        assert daily_saving_reminder() == 0
        assert len(mail.outbox) == 0

    def test_skips_user_without_email(self, destination):
        user = _make_user("+998900000003", email="", notify_daily=True)
        _make_trip(user, destination)

        assert daily_saving_reminder() == 0

    def test_skips_trip_whose_start_date_has_passed(self, destination):
        user = _make_user("+998900000004", email="d@example.com", notify_daily=True)
        _make_trip(user, destination, start_offset_days=-1)

        assert daily_saving_reminder() == 0

    def test_skips_already_fully_funded_trip(self, destination):
        user = _make_user("+998900000005", email="e@example.com", notify_daily=True)
        trip = _make_trip(user, destination, target_amount=Decimal("100"))
        SavingEntry.objects.create(trip=trip, amount=Decimal("150"), date=date.today())

        assert daily_saving_reminder() == 0


@pytest.mark.django_db
class TestWeeklyProgress:
    def test_reports_amount_saved_in_the_last_seven_days(self, destination):
        user = _make_user("+998900000006", email="f@example.com", notify_weekly=True)
        trip = _make_trip(user, destination)
        SavingEntry.objects.create(trip=trip, amount=Decimal("20"), date=date.today())
        SavingEntry.objects.create(trip=trip, amount=Decimal("15"), date=date.today() - timedelta(days=3))
        SavingEntry.objects.create(trip=trip, amount=Decimal("5"), date=date.today() - timedelta(days=10))

        sent = weekly_progress()

        assert sent == 1
        assert "$35" in mail.outbox[0].body


@pytest.mark.django_db
class TestStreakWarning:
    def _trip_with_streak(self, user, destination, streak_days):
        trip = _make_trip(user, destination)
        for offset in range(1, streak_days + 1):
            SavingEntry.objects.create(trip=trip, amount=Decimal("10"), date=date.today() - timedelta(days=offset))
        return trip

    def test_warns_when_streak_over_three_and_today_missing(self, destination):
        user = _make_user("+998900000007", email="g@example.com", notify_streak=True)
        self._trip_with_streak(user, destination, streak_days=5)

        assert streak_warning() == 1

    def test_silent_when_today_already_has_an_entry(self, destination):
        user = _make_user("+998900000008", email="h@example.com", notify_streak=True)
        trip = self._trip_with_streak(user, destination, streak_days=5)
        SavingEntry.objects.create(trip=trip, amount=Decimal("10"), date=date.today())

        assert streak_warning() == 0

    def test_silent_when_streak_is_not_over_three(self, destination):
        user = _make_user("+998900000009", email="i@example.com", notify_streak=True)
        self._trip_with_streak(user, destination, streak_days=2)

        assert streak_warning() == 0
