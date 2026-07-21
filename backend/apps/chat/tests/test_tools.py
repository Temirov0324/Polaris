from decimal import Decimal

import pytest

from apps.chat.services.tools import (
    _tool_add_saving_entry,
    _tool_calculate_budget,
    _tool_create_trip,
    _tool_get_user_trips,
    _tool_get_visa_info,
    _tool_suggest_destinations,
)
from apps.destinations.models import Country, Destination, PriceReference
from apps.users.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(phone="+998901234567", full_name="Test", password="testpass123")


@pytest.fixture
def turkey_destination(db):
    country = Country.objects.create(
        name_uz="Turkiya", name_en="Turkey", code="TR", visa_type="evisa", visa_cost_usd=20
    )
    destination = Destination.objects.create(country=country, city_uz="Istanbul", city_en="Istanbul")
    for month in range(1, 13):
        PriceReference.objects.create(
            destination=destination,
            month=month,
            flight_return_usd=Decimal("200"),
            hotel_night_econom=Decimal("15"),
            hotel_night_standard=Decimal("30"),
            hotel_night_comfort=Decimal("60"),
            food_day_econom=Decimal("8"),
            food_day_standard=Decimal("16"),
            food_day_comfort=Decimal("32"),
            transport_day_usd=Decimal("5"),
            activity_day_usd=Decimal("10"),
            confidence="high",
        )
    return destination


@pytest.mark.django_db
class TestCalculateBudgetTool:
    def test_finds_destination_and_returns_range(self, user, turkey_destination):
        result = _tool_calculate_budget(user, destination_city="Istanbul", duration_days=5, month=6)
        assert result["found"] is True
        assert result["destination"] == "Istanbul"
        assert result["budget_min_usd"] < result["budget_max_usd"]

    def test_unknown_city_reports_not_found(self, user, turkey_destination):
        result = _tool_calculate_budget(user, destination_city="Atlantis", duration_days=5, month=6)
        assert result["found"] is False


@pytest.mark.django_db
class TestVisaInfoTool:
    def test_finds_country_by_uzbek_name(self, user, turkey_destination):
        result = _tool_get_visa_info(user, country_name="Turkiya")
        assert result["found"] is True
        assert result["visa_type"] == "evisa"

    def test_unknown_country_reports_not_found(self, user, turkey_destination):
        result = _tool_get_visa_info(user, country_name="Narniya")
        assert result["found"] is False


@pytest.mark.django_db
class TestSuggestDestinationsTool:
    def test_filters_by_budget(self, user, turkey_destination):
        result = _tool_suggest_destinations(user, budget_usd=10000, duration_days=5, month=6)
        assert result["count"] == 1
        assert result["destinations"][0]["city"] == "Istanbul"

    def test_excludes_destinations_over_budget(self, user, turkey_destination):
        result = _tool_suggest_destinations(user, budget_usd=1, duration_days=5, month=6)
        assert result["count"] == 0


@pytest.mark.django_db
class TestGetUserTripsTool:
    def test_lists_trips_with_progress_when_target_set(self, user, turkey_destination):
        from datetime import date, timedelta

        from apps.savings.models import SavingEntry
        from apps.trips.models import Trip

        trip = Trip.objects.create(
            user=user,
            destination=turkey_destination,
            start_date=date.today() + timedelta(days=30),
            duration_days=5,
            budget_min=Decimal("500"),
            budget_max=Decimal("700"),
            target_amount=Decimal("600"),
        )
        SavingEntry.objects.create(trip=trip, amount=Decimal("60"), date=date.today())

        result = _tool_get_user_trips(user)
        assert len(result["trips"]) == 1
        assert result["trips"][0]["destination"] == "Istanbul"
        assert result["trips"][0]["saved_usd"] == 60.0

    def test_empty_when_no_trips(self, user):
        result = _tool_get_user_trips(user)
        assert result["trips"] == []


@pytest.mark.django_db
class TestCreateTripTool:
    def _future_date(self, days=30):
        from datetime import date, timedelta

        return (date.today() + timedelta(days=days)).isoformat()

    def test_creates_trip_with_computed_budget(self, user, turkey_destination):
        result = _tool_create_trip(
            user, destination_city="Istanbul", start_date=self._future_date(), duration_days=5
        )

        assert result["created"] is True
        assert result["destination"] == "Istanbul"
        assert result["budget_min_usd"] < result["budget_max_usd"]

        from apps.trips.models import Trip

        trip = Trip.objects.get(id=result["trip_id"])
        assert trip.user_id == user.id
        assert trip.duration_days == 5
        assert trip.target_amount is not None
        assert trip.breakdown is not None

    def test_honors_explicit_target_amount(self, user, turkey_destination):
        result = _tool_create_trip(
            user,
            destination_city="Istanbul",
            start_date=self._future_date(),
            duration_days=5,
            target_amount=999,
        )
        assert result["target_amount_usd"] == 999.0

    def test_unknown_destination_is_not_created(self, user, turkey_destination):
        result = _tool_create_trip(
            user, destination_city="Atlantis", start_date=self._future_date(), duration_days=5
        )
        assert result["created"] is False

    def test_invalid_date_format_is_rejected(self, user, turkey_destination):
        result = _tool_create_trip(
            user, destination_city="Istanbul", start_date="30-08-2026", duration_days=5
        )
        assert result["created"] is False

    def test_past_date_is_rejected(self, user, turkey_destination):
        result = _tool_create_trip(
            user, destination_city="Istanbul", start_date=self._future_date(-5), duration_days=5
        )
        assert result["created"] is False


@pytest.mark.django_db
class TestAddSavingEntryTool:
    def _make_trip(self, user, destination, target=Decimal("500")):
        from datetime import date, timedelta

        from apps.trips.models import Trip

        return Trip.objects.create(
            user=user,
            destination=destination,
            start_date=date.today() + timedelta(days=30),
            duration_days=5,
            budget_min=Decimal("400"),
            budget_max=Decimal("600"),
            target_amount=target,
            status=Trip.Status.SAVING,
        )

    def test_adds_entry_to_latest_active_trip(self, user, turkey_destination):
        trip = self._make_trip(user, turkey_destination)
        result = _tool_add_saving_entry(user, amount=15)
        assert result["saved"] is True
        assert result["trip_id"] == trip.id
        assert result["amount_usd"] == 15.0

    def test_adds_entry_to_explicit_trip_id(self, user, turkey_destination):
        trip = self._make_trip(user, turkey_destination)
        result = _tool_add_saving_entry(user, amount=20, trip_id=trip.id)
        assert result["saved"] is True
        assert result["trip_id"] == trip.id

    def test_upserts_the_same_date(self, user, turkey_destination):
        from apps.savings.models import SavingEntry

        self._make_trip(user, turkey_destination)
        _tool_add_saving_entry(user, amount=10)
        _tool_add_saving_entry(user, amount=25)

        assert SavingEntry.objects.count() == 1
        assert SavingEntry.objects.first().amount == Decimal("25")

    def test_no_active_trip_reports_failure(self, user):
        result = _tool_add_saving_entry(user, amount=10)
        assert result["saved"] is False

    def test_invalid_date_format_is_rejected(self, user, turkey_destination):
        self._make_trip(user, turkey_destination)
        result = _tool_add_saving_entry(user, amount=10, date="not-a-date")
        assert result["saved"] is False
