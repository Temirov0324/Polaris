import pytest
from rest_framework.test import APIClient

from apps.users.models import TelegramLinkCode, User

LINK_CODE_URL = "/api/v1/auth/telegram/link-code/"


@pytest.fixture
def user(db):
    return User.objects.create_user(phone="+998900000400", full_name="Test", password="testpass123", is_active=True)


@pytest.fixture
def client_for_user(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestTelegramLinkCode:
    def test_issues_code_and_deep_link_when_bot_configured(self, client_for_user, user, settings):
        settings.TELEGRAM_BOT_USERNAME = "PolarisAIBot"

        res = client_for_user.post(LINK_CODE_URL)

        assert res.status_code == 201
        assert res.data["data"]["bot_username"] == "PolarisAIBot"
        assert res.data["data"]["code"] in res.data["data"]["deep_link"]
        assert TelegramLinkCode.objects.filter(user=user, code=res.data["data"]["code"]).exists()

    def test_returns_503_when_bot_not_configured(self, client_for_user, settings):
        settings.TELEGRAM_BOT_USERNAME = ""

        res = client_for_user.post(LINK_CODE_URL)

        assert res.status_code == 503

    def test_requires_authentication(self, settings):
        settings.TELEGRAM_BOT_USERNAME = "PolarisAIBot"
        client = APIClient()

        res = client.post(LINK_CODE_URL)

        assert res.status_code == 401

    def test_me_endpoint_reports_telegram_linked_status(self, client_for_user, user):
        res = client_for_user.get("/api/v1/auth/me/")
        assert res.data["data"]["telegram_linked"] is False

        user.telegram_chat_id = "111"
        user.save(update_fields=["telegram_chat_id"])

        res = client_for_user.get("/api/v1/auth/me/")
        assert res.data["data"]["telegram_linked"] is True
