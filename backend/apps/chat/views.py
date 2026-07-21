from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.views import APIView

from apps.trips.models import Trip
from core.responses import envelope

from .exceptions import ChatRateLimitExceeded
from .models import ChatMessage
from .serializers import ChatMessageSerializer, ChatSendSerializer
from .services.agent import consume_rate_limit, send_message


class ChatMessageListView(generics.ListAPIView):
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        return ChatMessage.objects.filter(user=self.request.user)


class ChatSendView(APIView):
    def post(self, request):
        serializer = ChatSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        if not consume_rate_limit(request.user):
            raise ChatRateLimitExceeded()

        trip = None
        if v.get("trip_id"):
            trip = get_object_or_404(Trip, pk=v["trip_id"], user=request.user)

        reply = send_message(request.user, v["content"], trip=trip)
        return envelope({"message": reply}, status=201)
