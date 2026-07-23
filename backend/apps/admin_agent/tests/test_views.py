import json
from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.users.models import User


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(phone="+998900000001", full_name="Founder", password="testpass123")


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        phone="+998900000002", full_name="Staff", password="testpass123", is_staff=True
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(phone="+998900000003", full_name="Regular", password="testpass123")


@pytest.mark.django_db
class TestConsoleAccess:
    def test_anonymous_is_redirected_to_login(self, client):
        response = client.get(reverse("admin_agent:console"))
        assert response.status_code == 302
        assert "/admin/login/" in response.url

    def test_staff_but_not_superuser_is_redirected(self, client, staff_user):
        client.force_login(staff_user)
        response = client.get(reverse("admin_agent:console"))
        assert response.status_code == 302

    def test_regular_user_is_redirected(self, client, regular_user):
        client.force_login(regular_user)
        response = client.get(reverse("admin_agent:console"))
        assert response.status_code == 302

    def test_superuser_can_reach_the_console(self, client, superuser):
        client.force_login(superuser)
        response = client.get(reverse("admin_agent:console"))
        assert response.status_code == 200


@pytest.mark.django_db
class TestSendMessageEndpoint:
    def test_requires_superuser(self, client, regular_user):
        client.force_login(regular_user)
        response = client.post(
            reverse("admin_agent:message"), data=json.dumps({"message": "salom"}), content_type="application/json"
        )
        assert response.status_code == 302

    def test_rejects_empty_message(self, client, superuser):
        client.force_login(superuser)
        response = client.post(
            reverse("admin_agent:message"), data=json.dumps({"message": "  "}), content_type="application/json"
        )
        assert response.status_code == 400

    def test_reset_clears_session_history(self, client, superuser):
        client.force_login(superuser)
        session = client.session
        session["admin_agent_history"] = [{"role": "user", "content": "eski"}]
        session.save()

        response = client.post(
            reverse("admin_agent:message"), data=json.dumps({"reset": True}), content_type="application/json"
        )
        assert response.status_code == 200
        assert response.json()["history"] == []
        assert client.session.get("admin_agent_history") == []

    def test_successful_message_updates_session_history(self, client, superuser):
        client.force_login(superuser)
        with patch(
            "apps.admin_agent.views.handle_message",
            return_value={"reply": "Salom!", "history": [{"role": "user", "content": "salom"}], "actions": []},
        ):
            response = client.post(
                reverse("admin_agent:message"),
                data=json.dumps({"message": "salom"}),
                content_type="application/json",
            )

        assert response.status_code == 200
        assert response.json()["reply"] == "Salom!"
        assert client.session.get("admin_agent_history") == [{"role": "user", "content": "salom"}]
