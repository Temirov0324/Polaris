from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.destinations.models import Country, Destination, PriceReference
from apps.users.models import TelegramLinkCode, User

WEBHOOK_SECRET = "test-secret"


@pytest.fixture(autouse=True)
def telegram_settings(settings):
    settings.TELEGRAM_BOT_TOKEN = "fake-token"
    settings.TELEGRAM_WEBHOOK_SECRET = WEBHOOK_SECRET
    settings.TELEGRAM_BOT_USERNAME = "PolarisAIBot"


@pytest.fixture
def destination(db):
    country = Country.objects.create(
        name_uz="Birlashgan Arab Amirliklari", name_en="UAE", code="AE", visa_type="free", visa_cost_usd=0
    )
    dest = Destination.objects.create(country=country, city_uz="Dubay", city_en="Dubai")
    PriceReference.objects.create(
        destination=dest,
        month=date.today().month,
        flight_return_usd=Decimal("300"),
        hotel_night_econom=Decimal("30"),
        hotel_night_standard=Decimal("60"),
        hotel_night_comfort=Decimal("120"),
        food_day_econom=Decimal("15"),
        food_day_standard=Decimal("25"),
        food_day_comfort=Decimal("50"),
        transport_day_usd=Decimal("10"),
        activity_day_usd=Decimal("15"),
    )
    return dest


def webhook_url(secret=WEBHOOK_SECRET):
    return f"/api/v1/telegram/webhook/{secret}/"


def _message_update(chat_id, text):
    return {"message": {"chat": {"id": chat_id}, "text": text}}


@pytest.mark.django_db
class TestWebhookSecurity:
    def test_wrong_secret_returns_404(self):
        client = APIClient()
        res = client.post(webhook_url("wrong"), _message_update(1, "/help"), format="json")
        assert res.status_code == 404

    def test_correct_secret_returns_200(self):
        client = APIClient()
        res = client.post(webhook_url(), _message_update(1, "/help"), format="json")
        assert res.status_code == 200


@pytest.mark.django_db
class TestStartLinking:
    @patch("apps.telegram_bot.services.send_message")
    def test_valid_code_links_account(self, mock_send):
        user = User.objects.create_user(phone="+998900000300", full_name="Test", password="testpass123", is_active=True)
        link = TelegramLinkCode.issue(user)
        client = APIClient()

        res = client.post(webhook_url(), _message_update(555, f"/start {link.code}"), format="json")

        assert res.status_code == 200
        user.refresh_from_db()
        assert user.telegram_chat_id == "555"
        link.refresh_from_db()
        assert link.used_at is not None
        mock_send.assert_called_once()
        assert "bog'landi" in mock_send.call_args[0][1]

    @patch("apps.telegram_bot.services.send_message")
    def test_invalid_code_does_not_link(self, mock_send):
        client = APIClient()
        res = client.post(webhook_url(), _message_update(556, "/start not-a-real-code"), format="json")

        assert res.status_code == 200
        assert not User.objects.filter(telegram_chat_id="556").exists()
        mock_send.assert_called_once()
        assert "yaroqsiz" in mock_send.call_args[0][1]

    @patch("apps.telegram_bot.services.send_message")
    def test_start_without_code_sends_welcome(self, mock_send):
        client = APIClient()
        client.post(webhook_url(), _message_update(557, "/start"), format="json")

        mock_send.assert_called_once()
        assert "PolarisAI" in mock_send.call_args[0][1]

    @patch("apps.telegram_bot.services.send_message")
    def test_code_already_used_cannot_relink(self, mock_send):
        user = User.objects.create_user(
            phone="+998900000301", full_name="Test2", password="testpass123", is_active=True
        )
        link = TelegramLinkCode.issue(user)
        link.mark_used()
        client = APIClient()

        client.post(webhook_url(), _message_update(558, f"/start {link.code}"), format="json")

        user.refresh_from_db()
        assert user.telegram_chat_id is None
        assert "yaroqsiz" in mock_send.call_args[0][1]

    @patch("apps.telegram_bot.services.send_message")
    def test_chat_id_already_linked_to_another_user_is_rejected(self, mock_send):
        owner = User.objects.create_user(
            phone="+998900000302", full_name="Owner", password="testpass123", is_active=True
        )
        owner.telegram_chat_id = "999"
        owner.save(update_fields=["telegram_chat_id"])

        newcomer = User.objects.create_user(
            phone="+998900000303", full_name="New", password="testpass123", is_active=True
        )
        link = TelegramLinkCode.issue(newcomer)
        client = APIClient()

        client.post(webhook_url(), _message_update(999, f"/start {link.code}"), format="json")

        newcomer.refresh_from_db()
        assert newcomer.telegram_chat_id is None
        assert "allaqachon" in mock_send.call_args[0][1]


@pytest.mark.django_db
class TestBudgetCommand:
    @patch("apps.telegram_bot.services.send_message")
    def test_valid_command_returns_budget_range(self, mock_send, destination):
        client = APIClient()
        client.post(webhook_url(), _message_update(1, "/byudjet Dubay 5"), format="json")

        mock_send.assert_called_once()
        text = mock_send.call_args[0][1]
        assert "Dubay" in text
        assert "$" in text

    @patch("apps.telegram_bot.services.send_message")
    def test_unknown_city_gives_friendly_error(self, mock_send):
        client = APIClient()
        client.post(webhook_url(), _message_update(1, "/byudjet Atlantis 5"), format="json")

        assert "topilmadi" in mock_send.call_args[0][1]

    @patch("apps.telegram_bot.services.send_message")
    def test_missing_arguments_shows_format_hint(self, mock_send):
        client = APIClient()
        client.post(webhook_url(), _message_update(1, "/byudjet"), format="json")

        assert "Format" in mock_send.call_args[0][1]

    @patch("apps.telegram_bot.services.send_message")
    def test_non_numeric_days_is_rejected(self, mock_send, destination):
        client = APIClient()
        client.post(webhook_url(), _message_update(1, "/byudjet Dubay besh"), format="json")

        assert "butun son" in mock_send.call_args[0][1]


@pytest.mark.django_db
class TestOtherCommands:
    @patch("apps.telegram_bot.services.send_message")
    def test_help_lists_commands(self, mock_send):
        client = APIClient()
        client.post(webhook_url(), _message_update(1, "/help"), format="json")

        assert "/byudjet" in mock_send.call_args[0][1]

    @patch("apps.telegram_bot.services.send_message")
    def test_unrecognized_text_gets_fallback(self, mock_send):
        client = APIClient()
        client.post(webhook_url(), _message_update(1, "salom"), format="json")

        mock_send.assert_called_once()
