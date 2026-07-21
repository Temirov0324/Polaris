from rest_framework import serializers

from .models import SavingEntry


class SavingEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingEntry
        fields = ["id", "amount", "date", "note", "created_at"]
        read_only_fields = ["id", "created_at"]
