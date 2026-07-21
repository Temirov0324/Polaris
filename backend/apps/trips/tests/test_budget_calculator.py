from datetime import date
from decimal import Decimal

import pytest

from apps.destinations.models import Country, Destination, PriceReference
from apps.trips.services.budget_calculator import (
    calculate_budget,
    estimate_trip_budget,
    get_price_reference,
)


def _calc(**overrides):
    params = dict(
        flight_return_usd=Decimal("200"),
        hotel_night=Decimal("50"),
        food_day=Decimal("20"),
        transport_day_usd=Decimal("10"),
        activity_day_usd=Decimal("15"),
        visa_cost_usd=Decimal("30"),
        duration_days=5,
        travelers_count=2,
        confidence="high",
    )
    params.update(overrides)
    return calculate_budget(**params)


class TestCalculateBudget:
    def test_exact_amounts_for_two_travelers(self):
        result = _calc()

        assert result.flight == Decimal("400.00")
        assert result.accommodation == Decimal("200.00")
        assert result.food == Decimal("200.00")
        assert result.transport == Decimal("100.00")
        assert result.activities == Decimal("150.00")
        assert result.visa == Decimal("60.00")
        assert result.insurance == Decimal("15.00")
        assert result.subtotal == Decimal("1125.00")
        assert result.reserve == Decimal("168.75")
        assert result.total == Decimal("1293.75")
        assert result.budget_min == Decimal("1164.38")
        assert result.budget_max == Decimal("1487.81")

    def test_three_travelers_share_two_rooms(self):
        result = _calc(
            flight_return_usd=Decimal("100"),
            hotel_night=Decimal("40"),
            food_day=Decimal("15"),
            transport_day_usd=Decimal("5"),
            activity_day_usd=Decimal("5"),
            visa_cost_usd=Decimal("0"),
            duration_days=3,
            travelers_count=3,
        )

        # ceil(3 / 2) = 2 rooms, 2 nights -> 40 * 2 * 2
        assert result.accommodation == Decimal("160.00")
        assert result.total == Decimal("803.28")
        assert result.budget_min == Decimal("722.95")
        assert result.budget_max == Decimal("923.77")

    def test_one_day_trip_has_zero_accommodation(self):
        result = _calc(duration_days=1)
        assert result.accommodation == Decimal("0.00")

    def test_solo_traveler_needs_one_room(self):
        result = _calc(travelers_count=1, duration_days=4, hotel_night=Decimal("30"))
        # ceil(1 / 2) = 1 room, 3 nights
        assert result.accommodation == Decimal("90.00")

    def test_two_travelers_share_one_room(self):
        result = _calc(travelers_count=2, duration_days=4, hotel_night=Decimal("30"))
        # ceil(2 / 2) = 1 room, 3 nights
        assert result.accommodation == Decimal("90.00")

    def test_four_travelers_need_two_rooms(self):
        result = _calc(travelers_count=4, duration_days=4, hotel_night=Decimal("30"))
        # ceil(4 / 2) = 2 rooms, 3 nights
        assert result.accommodation == Decimal("180.00")

    def test_reserve_is_fifteen_percent_of_subtotal(self):
        result = _calc()
        expected_reserve = (result.subtotal * Decimal("0.15")).quantize(Decimal("0.01"))
        assert result.reserve == expected_reserve

    def test_budget_range_never_collapses_to_a_single_number(self):
        result = _calc()
        assert result.budget_min < result.total < result.budget_max

    def test_confidence_is_passed_through_unchanged(self):
        result = _calc(confidence="low")
        assert result.confidence == "low"

    def test_zero_duration_days_raises(self):
        with pytest.raises(ValueError):
            _calc(duration_days=0)

    def test_zero_travelers_raises(self):
        with pytest.raises(ValueError):
            _calc(travelers_count=0)

    def test_insurance_is_one_point_five_per_person_per_day(self):
        result = _calc(duration_days=6, travelers_count=3)
        assert result.insurance == Decimal("27.00")  # 1.5 * 6 * 3

    def test_as_dict_exposes_all_fields(self):
        result = _calc()
        data = result.as_dict()
        assert data["budget_min"] == result.budget_min
        assert data["confidence"] == result.confidence


@pytest.mark.django_db
class TestGetPriceReference:
    def _make_destination(self):
        country = Country.objects.create(
            name_uz="Turkiya", name_en="Turkey", code="TR", visa_type="evisa", visa_cost_usd=20
        )
        return Destination.objects.create(country=country, city_uz="Istanbul", city_en="Istanbul")

    def _make_price(self, destination, month, confidence="high"):
        return PriceReference.objects.create(
            destination=destination,
            month=month,
            flight_return_usd=Decimal("200"),
            hotel_night_econom=Decimal("20"),
            hotel_night_standard=Decimal("40"),
            hotel_night_comfort=Decimal("80"),
            food_day_econom=Decimal("10"),
            food_day_standard=Decimal("20"),
            food_day_comfort=Decimal("40"),
            transport_day_usd=Decimal("5"),
            activity_day_usd=Decimal("10"),
            confidence=confidence,
        )

    def test_exact_month_match(self):
        destination = self._make_destination()
        june = self._make_price(destination, month=6)

        price_ref, is_exact = get_price_reference(destination, 6)

        assert price_ref == june
        assert is_exact is True

    def test_falls_back_to_nearest_month(self):
        destination = self._make_destination()
        march = self._make_price(destination, month=3)
        self._make_price(destination, month=9)

        price_ref, is_exact = get_price_reference(destination, 2)

        assert price_ref == march  # |3-2|=1 is closer than |9-2|=7
        assert is_exact is False

    def test_wraps_around_year_boundary(self):
        destination = self._make_destination()
        december = self._make_price(destination, month=12)
        self._make_price(destination, month=6)

        price_ref, is_exact = get_price_reference(destination, 1)

        assert price_ref == december  # distance(12, 1) == 1, shorter than the mid-year gap
        assert is_exact is False

    def test_raises_when_no_price_reference_exists(self):
        destination = self._make_destination()
        with pytest.raises(PriceReference.DoesNotExist):
            get_price_reference(destination, 1)


@pytest.mark.django_db
class TestEstimateTripBudget:
    def test_uses_low_confidence_on_fallback_month(self):
        country = Country.objects.create(
            name_uz="Gruziya", name_en="Georgia", code="GE", visa_type="free", visa_cost_usd=0
        )
        destination = Destination.objects.create(country=country, city_uz="Tbilisi", city_en="Tbilisi")
        PriceReference.objects.create(
            destination=destination,
            month=7,
            flight_return_usd=Decimal("150"),
            hotel_night_econom=Decimal("15"),
            hotel_night_standard=Decimal("30"),
            hotel_night_comfort=Decimal("60"),
            food_day_econom=Decimal("8"),
            food_day_standard=Decimal("16"),
            food_day_comfort=Decimal("32"),
            transport_day_usd=Decimal("4"),
            activity_day_usd=Decimal("8"),
            confidence="high",
        )

        result = estimate_trip_budget(
            destination=destination,
            start_date=date(2026, 1, 10),
            duration_days=5,
            travelers_count=2,
            style="standard",
        )

        assert result.confidence == "low"
        assert result.budget_min < result.budget_max
