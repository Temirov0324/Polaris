from unittest.mock import patch

import pytest

from apps.admin_agent.services.tools import TOOL_HANDLERS, execute_tool
from apps.destinations.models import Country, Destination, PriceReference


@pytest.fixture
def country(db):
    return Country.objects.create(
        name_uz="Turkiya", name_en="Turkey", code="TR", visa_type="evisa", visa_cost_usd=20
    )


@pytest.fixture
def destination(db, country):
    return Destination.objects.create(country=country, city_uz="Istanbul", city_en="Istanbul")


class TestScopeIsRestrictedToCatalogData:
    def test_tool_handlers_only_cover_catalog_tools(self):
        # Locks the allowlist down: any new tool must be added here on
        # purpose, so a future edit can't accidentally hand this agent a
        # tool that reaches into User/Trip/SavingEntry/ChatMessage.
        # research_destinations_online is read-only (Google Search only) —
        # it never touches the database itself, so it's exempt from the
        # "writes only to catalog data" concern this test otherwise locks.
        assert set(TOOL_HANDLERS.keys()) == {
            "list_countries",
            "upsert_country",
            "list_destinations",
            "upsert_destination",
            "get_price_status",
            "upsert_price_reference",
            "research_destinations_online",
        }


@pytest.mark.django_db
class TestUpsertCountry:
    def test_creates_new_country(self):
        result = execute_tool(
            "upsert_country",
            {
                "code": "ge",
                "name_uz": "Gruziya",
                "name_en": "Georgia",
                "visa_type": "free",
                "visa_cost_usd": 0,
            },
        )
        assert result["ok"] is True
        assert result["created"] is True
        assert Country.objects.filter(code="GE").exists()

    def test_updates_existing_country_by_code(self, country):
        result = execute_tool(
            "upsert_country",
            {
                "code": "TR",
                "name_uz": "Turkiya yangi",
                "name_en": "Turkey",
                "visa_type": "free",
                "visa_cost_usd": 0,
            },
        )
        assert result["ok"] is True
        assert result["created"] is False
        country.refresh_from_db()
        assert country.name_uz == "Turkiya yangi"
        assert country.visa_type == "free"

    def test_rejects_invalid_country_code(self):
        result = execute_tool(
            "upsert_country",
            {"code": "TUR", "name_uz": "x", "name_en": "x", "visa_type": "free", "visa_cost_usd": 0},
        )
        assert result["ok"] is False
        assert Country.objects.count() == 0

    def test_rejects_invalid_visa_type(self):
        result = execute_tool(
            "upsert_country",
            {"code": "FR", "name_uz": "Fransiya", "name_en": "France", "visa_type": "made_up", "visa_cost_usd": 0},
        )
        assert result["ok"] is False

    def test_rejects_negative_visa_cost(self):
        result = execute_tool(
            "upsert_country",
            {"code": "FR", "name_uz": "Fransiya", "name_en": "France", "visa_type": "free", "visa_cost_usd": -5},
        )
        assert result["ok"] is False


@pytest.mark.django_db
class TestUpsertDestination:
    def test_creates_new_destination(self, country):
        result = execute_tool(
            "upsert_destination",
            {"country_code": "tr", "city_uz": "Antalya", "city_en": "Antalya"},
        )
        assert result["ok"] is True
        assert result["created"] is True
        assert Destination.objects.filter(city_uz="Antalya", country=country).exists()

    def test_updates_existing_destination_case_insensitively(self, destination):
        result = execute_tool(
            "upsert_destination",
            {
                "country_code": "TR",
                "city_uz": "istanbul",
                "city_en": "Istanbul",
                "is_popular": True,
            },
        )
        assert result["ok"] is True
        assert result["created"] is False
        destination.refresh_from_db()
        assert destination.is_popular is True
        assert Destination.objects.count() == 1

    def test_rejects_unknown_country_code(self):
        result = execute_tool(
            "upsert_destination", {"country_code": "ZZ", "city_uz": "Ghost City", "city_en": "Ghost City"}
        )
        assert result["ok"] is False
        assert Destination.objects.count() == 0


@pytest.mark.django_db
class TestUpsertPriceReference:
    def test_creates_price_reference(self, destination):
        result = execute_tool(
            "upsert_price_reference",
            {
                "city": "Istanbul",
                "month": 7,
                "flight_return_usd": 220,
                "hotel_night_econom": 18,
                "hotel_night_standard": 28,
                "hotel_night_comfort": 45,
                "food_day_econom": 12,
                "food_day_standard": 20,
                "food_day_comfort": 35,
                "transport_day_usd": 8,
                "activity_day_usd": 10,
            },
        )
        assert result["ok"] is True
        assert result["created"] is True
        assert PriceReference.objects.filter(destination=destination, month=7).exists()

    def test_updates_on_repeat_call_for_same_month(self, destination):
        base_args = {
            "city": "Istanbul",
            "month": 7,
            "flight_return_usd": 220,
            "hotel_night_econom": 18,
            "hotel_night_standard": 28,
            "hotel_night_comfort": 45,
            "food_day_econom": 12,
            "food_day_standard": 20,
            "food_day_comfort": 35,
            "transport_day_usd": 8,
            "activity_day_usd": 10,
        }
        execute_tool("upsert_price_reference", base_args)
        result = execute_tool("upsert_price_reference", {**base_args, "flight_return_usd": 250})

        assert result["ok"] is True
        assert result["created"] is False
        assert PriceReference.objects.filter(destination=destination, month=7).count() == 1
        assert PriceReference.objects.get(destination=destination, month=7).flight_return_usd == 250

    def test_rejects_unknown_destination(self):
        result = execute_tool(
            "upsert_price_reference",
            {
                "city": "Nowhere",
                "month": 7,
                "flight_return_usd": 220,
                "hotel_night_econom": 18,
                "hotel_night_standard": 28,
                "hotel_night_comfort": 45,
                "food_day_econom": 12,
                "food_day_standard": 20,
                "food_day_comfort": 35,
                "transport_day_usd": 8,
                "activity_day_usd": 10,
            },
        )
        assert result["ok"] is False

    def test_rejects_out_of_range_month(self, destination):
        result = execute_tool(
            "upsert_price_reference",
            {
                "city": "Istanbul",
                "month": 13,
                "flight_return_usd": 220,
                "hotel_night_econom": 18,
                "hotel_night_standard": 28,
                "hotel_night_comfort": 45,
                "food_day_econom": 12,
                "food_day_standard": 20,
                "food_day_comfort": 35,
                "transport_day_usd": 8,
                "activity_day_usd": 10,
            },
        )
        assert result["ok"] is False

    def test_rejects_zero_or_negative_price(self, destination):
        result = execute_tool(
            "upsert_price_reference",
            {
                "city": "Istanbul",
                "month": 7,
                "flight_return_usd": 0,
                "hotel_night_econom": 18,
                "hotel_night_standard": 28,
                "hotel_night_comfort": 45,
                "food_day_econom": 12,
                "food_day_standard": 20,
                "food_day_comfort": 35,
                "transport_day_usd": 8,
                "activity_day_usd": 10,
            },
        )
        assert result["ok"] is False
        assert PriceReference.objects.count() == 0

    def test_rejects_implausibly_high_price(self, destination):
        result = execute_tool(
            "upsert_price_reference",
            {
                "city": "Istanbul",
                "month": 7,
                "flight_return_usd": 220,
                "hotel_night_econom": 18,
                "hotel_night_standard": 28,
                "hotel_night_comfort": 45,
                "food_day_econom": 12,
                "food_day_standard": 20,
                "food_day_comfort": 35,
                "transport_day_usd": 8,
                # Looks like a monthly figure typed into a daily field.
                "activity_day_usd": 50000,
            },
        )
        assert result["ok"] is False
        assert PriceReference.objects.count() == 0

    def test_rejects_implausibly_low_price(self, destination):
        result = execute_tool(
            "upsert_price_reference",
            {
                "city": "Istanbul",
                "month": 7,
                "flight_return_usd": 220,
                "hotel_night_econom": 0.5,
                "hotel_night_standard": 28,
                "hotel_night_comfort": 45,
                "food_day_econom": 12,
                "food_day_standard": 20,
                "food_day_comfort": 35,
                "transport_day_usd": 8,
                "activity_day_usd": 10,
            },
        )
        assert result["ok"] is False
        assert PriceReference.objects.count() == 0


class TestResearchDestinationsOnline:
    def test_delegates_to_run_web_research(self):
        with patch("apps.admin_agent.services.research.run_web_research") as mocked:
            mocked.return_value = {"ok": True, "findings": "...", "sources": []}
            result = execute_tool("research_destinations_online", {"country_name": "Tailand", "city_count": 5})

        mocked.assert_called_once_with("Tailand", 5)
        assert result["ok"] is True

    def test_defaults_city_count_when_omitted(self):
        with patch("apps.admin_agent.services.research.run_web_research") as mocked:
            mocked.return_value = {"ok": True, "findings": "...", "sources": []}
            execute_tool("research_destinations_online", {"country_name": "Tailand"})

        mocked.assert_called_once_with("Tailand", 5)


@pytest.mark.django_db
class TestListAndStatusTools:
    def test_list_countries_returns_created_country(self, country):
        result = execute_tool("list_countries", {})
        assert result["countries"][0]["code"] == "TR"

    def test_list_destinations_filters_by_country(self, destination):
        result = execute_tool("list_destinations", {"country_code": "TR"})
        assert len(result["destinations"]) == 1
        result_other = execute_tool("list_destinations", {"country_code": "GE"})
        assert result_other["destinations"] == []

    def test_get_price_status_reports_missing_months(self, destination):
        execute_tool(
            "upsert_price_reference",
            {
                "city": "Istanbul",
                "month": 7,
                "flight_return_usd": 220,
                "hotel_night_econom": 18,
                "hotel_night_standard": 28,
                "hotel_night_comfort": 45,
                "food_day_econom": 12,
                "food_day_standard": 20,
                "food_day_comfort": 35,
                "transport_day_usd": 8,
                "activity_day_usd": 10,
            },
        )
        result = execute_tool("get_price_status", {"city": "Istanbul"})
        assert result["months_filled"] == [7]
        assert 7 not in result["months_missing"]
        assert len(result["months_missing"]) == 11


def test_execute_tool_rejects_unknown_tool_name():
    result = execute_tool("delete_all_users", {})
    assert result["ok"] is False
