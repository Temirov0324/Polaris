import logging

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import handle_update

logger = logging.getLogger(__name__)


class TelegramWebhookView(APIView):
    """The URL's secret path segment is the auth mechanism -- Telegram
    doesn't sign webhook requests, so this is the standard lightweight
    guard (matches what's registered via setWebhook)."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request, secret):
        if not settings.TELEGRAM_WEBHOOK_SECRET or secret != settings.TELEGRAM_WEBHOOK_SECRET:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            handle_update(request.data)
        except Exception:
            logger.exception("Failed to handle Telegram update")
        return Response(status=status.HTTP_200_OK)
