import pytest
from rest_framework.test import APIClient

from apps.analytics.models import AnalyticsEvent
from apps.users.models import User

TRACK_URL = "/api/v1/analytics/track/"


@pytest.mark.django_db
class TestTrackEvent:
    def test_anonymous_event_is_recorded(self):
        client = APIClient()
        res = client.post(TRACK_URL, {"event": "landing_viewed", "anon_id": "abc123"}, format="json")

        assert res.status_code == 201
        event = AnalyticsEvent.objects.get()
        assert event.name == "landing_viewed"
        assert event.anon_id == "abc123"
        assert event.user is None

    def test_authenticated_event_records_user(self):
        user = User.objects.create_user(phone="+998900000200", full_name="Test", password="testpass123")
        client = APIClient()
        client.force_authenticate(user=user)

        res = client.post(TRACK_URL, {"event": "trip_created", "properties": {"destination_id": 3}}, format="json")

        assert res.status_code == 201
        event = AnalyticsEvent.objects.get()
        assert event.user == user
        assert event.properties == {"destination_id": 3}

    def test_missing_event_name_is_rejected_without_error(self):
        client = APIClient()
        res = client.post(TRACK_URL, {}, format="json")

        assert res.status_code == 400
        assert AnalyticsEvent.objects.count() == 0

    def test_overlong_event_name_is_rejected(self):
        client = APIClient()
        res = client.post(TRACK_URL, {"event": "x" * 200}, format="json")

        assert res.status_code == 400
        assert AnalyticsEvent.objects.count() == 0
