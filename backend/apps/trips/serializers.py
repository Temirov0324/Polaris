from rest_framework import serializers

from apps.destinations.models import Destination
from apps.destinations.serializers import DestinationListSerializer

from .models import BudgetBreakdown, Trip


class TripEstimateRequestSerializer(serializers.Serializer):
    destination = serializers.PrimaryKeyRelatedField(queryset=Destination.objects.all())
    start_date = serializers.DateField()
    duration_days = serializers.IntegerField(min_value=1)
    travelers_count = serializers.IntegerField(min_value=1, default=1)
    style = serializers.ChoiceField(choices=Trip.Style.choices, default=Trip.Style.STANDARD)


class BudgetBreakdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetBreakdown
        fields = ["flight", "accommodation", "food", "transport", "activities", "visa", "insurance", "reserve"]


class TripSerializer(serializers.ModelSerializer):
    destination_detail = DestinationListSerializer(source="destination", read_only=True)
    breakdown = BudgetBreakdownSerializer(read_only=True)

    class Meta:
        model = Trip
        fields = [
            "id",
            "destination",
            "destination_detail",
            "start_date",
            "duration_days",
            "travelers_count",
            "style",
            "budget_min",
            "budget_max",
            "target_amount",
            "status",
            "created_at",
            "breakdown",
        ]
        read_only_fields = ["id", "budget_min", "budget_max", "status", "created_at", "breakdown"]


class TripUpdateSerializer(serializers.ModelSerializer):
    """PATCH only touches the fields a user can change after a trip is
    created — the destination/dates/budget stay fixed since they were
    computed together by the estimator."""

    class Meta:
        model = Trip
        fields = ["target_amount", "status"]
