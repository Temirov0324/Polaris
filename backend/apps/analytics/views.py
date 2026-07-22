from rest_framework import permissions
from rest_framework.views import APIView

from core.responses import envelope

from .models import AnalyticsEvent
from .serializers import TrackEventSerializer


class TrackEventView(APIView):
    """Public by design — half the funnel (landing, registration) happens
    before a user has a session. Never raises on bad input: analytics must
    not be able to break the product it's observing."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TrackEventSerializer(data=request.data)
        if not serializer.is_valid():
            return envelope({"ok": False}, status=400)
        v = serializer.validated_data

        AnalyticsEvent.objects.create(
            name=v["event"],
            user=request.user if request.user.is_authenticated else None,
            anon_id=v.get("anon_id", ""),
            properties=v.get("properties") or {},
        )
        return envelope({"ok": True}, status=201)
