from rest_framework import serializers

from .models import SavingEntry


class SavingEntrySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True, default="")

    class Meta:
        model = SavingEntry
        fields = ["id", "amount", "date", "note", "user_name", "created_at"]
        read_only_fields = ["id", "user_name", "created_at"]
