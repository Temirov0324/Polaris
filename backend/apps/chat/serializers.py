from rest_framework import serializers

from .models import ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "created_at"]


class ChatSendSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=2000, allow_blank=False)
    trip_id = serializers.IntegerField(required=False, allow_null=True)
