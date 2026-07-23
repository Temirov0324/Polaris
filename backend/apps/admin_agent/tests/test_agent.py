from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from apps.admin_agent.models import AdminAgentLog
from apps.admin_agent.services.agent import handle_message
from apps.destinations.models import Country
from apps.users.models import User


def _text_response(text):
    return SimpleNamespace(text=text, function_calls=[], candidates=[])


def _function_call_response(name, args):
    function_call = SimpleNamespace(name=name, args=args)
    part = SimpleNamespace(function_call=function_call)
    candidate = SimpleNamespace(content=SimpleNamespace(parts=[part]))
    return SimpleNamespace(text="", function_calls=[function_call], candidates=[candidate])


@pytest.fixture
def founder(db):
    return User.objects.create_superuser(phone="+998900000001", full_name="Founder", password="testpass123")


@pytest.mark.django_db
class TestHandleMessage:
    def test_without_api_key_returns_not_configured_message(self, founder, settings):
        settings.GEMINI_ADMIN_API_KEY = ""
        result = handle_message(founder, "Turkiya haqida ma'lumot qo'sh", [])
        assert "sozlanmagan" in result["reply"]
        assert result["actions"] == []

    def test_plain_reply_with_no_tool_calls(self, founder, settings):
        settings.GEMINI_ADMIN_API_KEY = "fake-key"
        client = MagicMock()
        client.models.generate_content.return_value = _text_response("Qanday ma'lumot qo'shmoqchisiz?")

        with patch("apps.admin_agent.services.agent._get_client", return_value=client):
            result = handle_message(founder, "Salom", [])

        assert result["reply"] == "Qanday ma'lumot qo'shmoqchisiz?"
        assert result["history"][-1] == {"role": "assistant", "content": result["reply"]}
        assert result["actions"] == []

    def test_falls_back_on_api_error(self, founder, settings):
        settings.GEMINI_ADMIN_API_KEY = "fake-key"
        client = MagicMock()
        client.models.generate_content.side_effect = RuntimeError("boom")

        with patch("apps.admin_agent.services.agent._get_client", return_value=client):
            result = handle_message(founder, "Turkiya qo'sh", [])

        assert result["reply"] == "Hozir javob bera olmadim, birozdan keyin urinib ko'ring"

    def test_executes_tool_and_logs_it(self, founder, settings):
        settings.GEMINI_ADMIN_API_KEY = "fake-key"
        client = MagicMock()
        client.models.generate_content.side_effect = [
            _function_call_response(
                "upsert_country",
                {
                    "code": "GE",
                    "name_uz": "Gruziya",
                    "name_en": "Georgia",
                    "visa_type": "free",
                    "visa_cost_usd": 0,
                },
            ),
            _text_response("Gruziya qo'shildi."),
        ]

        with patch("apps.admin_agent.services.agent._get_client", return_value=client):
            result = handle_message(founder, "Gruziyani vizasiz qo'sh", [])

        assert result["reply"] == "Gruziya qo'shildi."
        assert Country.objects.filter(code="GE").exists()

        log = AdminAgentLog.objects.get()
        assert log.tool_name == "upsert_country"
        assert log.performed_by == founder
        assert log.success is True

    def test_failed_tool_call_is_logged_as_unsuccessful(self, founder, settings):
        settings.GEMINI_ADMIN_API_KEY = "fake-key"
        client = MagicMock()
        client.models.generate_content.side_effect = [
            _function_call_response("upsert_country", {"code": "TOO_LONG", "name_uz": "x", "name_en": "x",
                                                          "visa_type": "free", "visa_cost_usd": 0}),
            _text_response("Kod noto'g'ri edi, qaytadan kiriting."),
        ]

        with patch("apps.admin_agent.services.agent._get_client", return_value=client):
            handle_message(founder, "X mamlakatni qo'sh", [])

        log = AdminAgentLog.objects.get()
        assert log.success is False

    def test_history_round_trips_through_the_call(self, founder, settings):
        settings.GEMINI_ADMIN_API_KEY = "fake-key"
        client = MagicMock()
        client.models.generate_content.return_value = _text_response("ok")
        history = [{"role": "user", "content": "avvalgi xabar"}, {"role": "assistant", "content": "avvalgi javob"}]

        with patch("apps.admin_agent.services.agent._get_client", return_value=client):
            result = handle_message(founder, "yangi xabar", history)

        assert result["history"][0] == history[0]
        assert result["history"][-2] == {"role": "user", "content": "yangi xabar"}
