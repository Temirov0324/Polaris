from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from apps.chat.models import ChatMessage
from apps.chat.services.agent import DAILY_MESSAGE_LIMIT, consume_rate_limit, send_message
from apps.users.models import User


def _text_response(text):
    return SimpleNamespace(text=text, function_calls=[], candidates=[])


def _function_call_response(name, args):
    function_call = SimpleNamespace(name=name, args=args)
    part = SimpleNamespace(function_call=function_call)
    candidate = SimpleNamespace(content=SimpleNamespace(parts=[part]))
    return SimpleNamespace(text="", function_calls=[function_call], candidates=[candidate])


@pytest.fixture
def user(db):
    return User.objects.create_user(phone="+998901234567", full_name="Test", password="testpass123")


@pytest.mark.django_db
class TestConsumeRateLimit:
    def test_allows_up_to_the_daily_limit(self, user):
        for _ in range(DAILY_MESSAGE_LIMIT):
            assert consume_rate_limit(user) is True

    def test_blocks_once_the_limit_is_reached(self, user):
        for _ in range(DAILY_MESSAGE_LIMIT):
            consume_rate_limit(user)
        assert consume_rate_limit(user) is False

    def test_different_users_have_independent_limits(self, user):
        other = User.objects.create_user(phone="+998907654321", full_name="Other", password="testpass123")
        for _ in range(DAILY_MESSAGE_LIMIT):
            consume_rate_limit(user)
        assert consume_rate_limit(user) is False
        assert consume_rate_limit(other) is True


@pytest.mark.django_db
class TestSendMessage:
    def test_persists_user_and_assistant_messages(self, user):
        client = MagicMock()
        client.models.generate_content.return_value = _text_response("Salom! Sizga qanday yordam bera olaman?")

        with patch("apps.chat.services.agent._get_client", return_value=client):
            reply = send_message(user, "Salom")

        assert reply == "Salom! Sizga qanday yordam bera olaman?"
        messages = list(ChatMessage.objects.filter(user=user).order_by("created_at"))
        assert [m.role for m in messages] == ["user", "assistant"]
        assert messages[0].content == "Salom"
        assert messages[1].content == reply

    def test_falls_back_to_generic_message_on_api_error(self, user):
        client = MagicMock()
        client.models.generate_content.side_effect = RuntimeError("boom")

        with patch("apps.chat.services.agent._get_client", return_value=client):
            reply = send_message(user, "Turkiyaga qancha kerak?")

        assert reply == "Hozir javob bera olmadim, birozdan keyin urinib ko'ring"
        assert ChatMessage.objects.filter(user=user, role="assistant", content=reply).exists()

    def test_executes_tool_then_returns_final_text(self, user):
        client = MagicMock()
        client.models.generate_content.side_effect = [
            _function_call_response("get_visa_info", {"country_name": "Turkiya"}),
            _text_response("Turkiyaga elektron viza kerak, narxi taxminan $20."),
        ]

        with patch("apps.chat.services.agent._get_client", return_value=client):
            reply = send_message(user, "Turkiyaga viza kerakmi?")

        assert reply == "Turkiyaga elektron viza kerak, narxi taxminan $20."
        assert client.models.generate_content.call_count == 2

    def test_uses_last_ten_messages_as_context(self, user):
        for i in range(12):
            ChatMessage.objects.create(user=user, role="user", content=f"eski xabar {i}")

        client = MagicMock()
        client.models.generate_content.return_value = _text_response("ok")

        with patch("apps.chat.services.agent._get_client", return_value=client):
            send_message(user, "yangi savol")

        sent_contents = client.models.generate_content.call_args.kwargs["contents"]
        assert len(sent_contents) == 10
        assert sent_contents[-1].parts[0].text == "yangi savol"
