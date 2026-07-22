from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient

from apps.users.models import User, VerificationCode

REGISTER_URL = "/api/v1/auth/register/"
RESEND_URL = "/api/v1/auth/register/resend/"
VERIFY_URL = "/api/v1/auth/register/verify/"
LOGIN_URL = "/api/v1/auth/login/"
RESET_URL = "/api/v1/auth/password-reset/"
RESET_CONFIRM_URL = "/api/v1/auth/password-reset/confirm/"


@pytest.fixture
def client():
    return APIClient()


def _register_payload(**overrides):
    payload = dict(
        full_name="Test User",
        phone="+998901234567",
        email="test@example.com",
        password="testpass123",
    )
    payload.update(overrides)
    return payload


@pytest.mark.django_db
class TestRegisterRequest:
    def test_creates_inactive_user_and_sends_code(self, client):
        res = client.post(REGISTER_URL, _register_payload(), format="json")

        assert res.status_code == 201
        user = User.objects.get(phone="+998901234567")
        assert user.is_active is False
        assert len(mail.outbox) == 1
        assert user.email in mail.outbox[0].to

    def test_duplicate_active_phone_rejected(self, client):
        User.objects.create_user(phone="+998901234567", full_name="X", password="p", is_active=True)
        res = client.post(REGISTER_URL, _register_payload(), format="json")
        assert res.status_code == 400

    def test_duplicate_active_email_rejected(self, client):
        User.objects.create_user(
            phone="+998909999999", full_name="X", password="p", email="test@example.com", is_active=True
        )
        res = client.post(REGISTER_URL, _register_payload(), format="json")
        assert res.status_code == 400

    def test_abandoned_registration_is_overwritten(self, client):
        client.post(REGISTER_URL, _register_payload(), format="json")
        assert User.objects.filter(phone="+998901234567").count() == 1

        res = client.post(REGISTER_URL, _register_payload(full_name="Retry"), format="json")
        assert res.status_code == 201
        assert User.objects.filter(phone="+998901234567").count() == 1
        assert User.objects.get(phone="+998901234567").full_name == "Retry"


@pytest.mark.django_db
class TestRegisterVerify:
    def _register(self, client):
        client.post(REGISTER_URL, _register_payload(), format="json")
        user = User.objects.get(phone="+998901234567")
        code = user.verification_codes.filter(purpose=VerificationCode.Purpose.REGISTER).latest("created_at")
        return user, code

    def test_correct_code_activates_and_logs_in(self, client):
        user, code = self._register(client)

        res = client.post(VERIFY_URL, {"email": user.email, "code": code.code}, format="json")

        assert res.status_code == 200
        user.refresh_from_db()
        assert user.is_active is True
        assert "access_token" in res.cookies

    def test_wrong_code_rejected_and_does_not_activate(self, client):
        user, code = self._register(client)

        res = client.post(VERIFY_URL, {"email": user.email, "code": "000000"}, format="json")

        assert res.status_code == 400
        user.refresh_from_db()
        assert user.is_active is False

    def test_too_many_wrong_attempts_locks_code(self, client):
        user, code = self._register(client)

        for _ in range(VerificationCode.MAX_ATTEMPTS):
            client.post(VERIFY_URL, {"email": user.email, "code": "000000"}, format="json")

        res = client.post(VERIFY_URL, {"email": user.email, "code": code.code}, format="json")
        assert res.status_code == 400

    def test_unknown_email_rejected(self, client):
        res = client.post(VERIFY_URL, {"email": "nope@example.com", "code": "123456"}, format="json")
        assert res.status_code == 400


@pytest.mark.django_db
class TestRegisterResend:
    def test_resend_issues_new_code_after_cooldown(self, client):
        client.post(REGISTER_URL, _register_payload(), format="json")
        user = User.objects.get(phone="+998901234567")
        past = timezone.now() - timedelta(seconds=VerificationCode.RESEND_COOLDOWN_SECONDS + 1)
        user.verification_codes.update(created_at=past)

        res = client.post(RESEND_URL, {"email": "test@example.com"}, format="json")
        assert res.status_code == 200
        assert len(mail.outbox) == 2

    def test_resend_blocked_during_cooldown(self, client):
        client.post(REGISTER_URL, _register_payload(), format="json")
        res = client.post(RESEND_URL, {"email": "test@example.com"}, format="json")
        assert res.status_code == 400


@pytest.mark.django_db
class TestLoginRequiresVerification:
    def test_unverified_user_cannot_login(self, client):
        client.post(REGISTER_URL, _register_payload(), format="json")
        res = client.post(LOGIN_URL, {"phone": "+998901234567", "password": "testpass123"}, format="json")
        assert res.status_code == 400
        assert "tasdiqlanmagan" in res.data["error"]["message_uz"]

    def test_verified_user_can_login(self, client):
        client.post(REGISTER_URL, _register_payload(), format="json")
        user = User.objects.get(phone="+998901234567")
        code = user.verification_codes.latest("created_at")
        client.post(VERIFY_URL, {"email": user.email, "code": code.code}, format="json")

        res = client.post(LOGIN_URL, {"phone": "+998901234567", "password": "testpass123"}, format="json")
        assert res.status_code == 200


@pytest.mark.django_db
class TestPasswordReset:
    @pytest.fixture
    def verified_user(self):
        return User.objects.create_user(
            phone="+998901234567", full_name="Test", email="test@example.com", password="oldpass123", is_active=True
        )

    def test_request_sends_code_for_existing_user(self, client, verified_user):
        res = client.post(RESET_URL, {"email": "test@example.com"}, format="json")
        assert res.status_code == 200
        assert len(mail.outbox) == 1

    def test_request_does_not_leak_unknown_email(self, client):
        res = client.post(RESET_URL, {"email": "nobody@example.com"}, format="json")
        assert res.status_code == 200
        assert len(mail.outbox) == 0

    def test_confirm_with_correct_code_changes_password(self, client, verified_user):
        client.post(RESET_URL, {"email": "test@example.com"}, format="json")
        code = verified_user.verification_codes.latest("created_at")

        res = client.post(
            RESET_CONFIRM_URL,
            {"email": "test@example.com", "code": code.code, "new_password": "newpass123"},
            format="json",
        )
        assert res.status_code == 200

        login_res = client.post(LOGIN_URL, {"phone": "+998901234567", "password": "newpass123"}, format="json")
        assert login_res.status_code == 200

    def test_confirm_with_wrong_code_rejected(self, client, verified_user):
        client.post(RESET_URL, {"email": "test@example.com"}, format="json")

        res = client.post(
            RESET_CONFIRM_URL,
            {"email": "test@example.com", "code": "000000", "new_password": "newpass123"},
            format="json",
        )
        assert res.status_code == 400
