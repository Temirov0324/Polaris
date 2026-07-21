from django.db import transaction
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from apps.destinations.models import PriceReference
from apps.destinations.serializers import DestinationListSerializer
from core.responses import envelope

from .models import BudgetBreakdown, Trip
from .serializers import TripEstimateRequestSerializer, TripSerializer, TripUpdateSerializer
from .services.budget_calculator import estimate_trip_budget


def _estimate_or_404(*, destination, start_date, duration_days, travelers_count, style):
    try:
        return estimate_trip_budget(
            destination=destination,
            start_date=start_date,
            duration_days=duration_days,
            travelers_count=travelers_count,
            style=style,
        )
    except PriceReference.DoesNotExist:
        raise NotFound("Bu yo'nalish uchun narx ma'lumoti hali kiritilmagan")


def _breakdown_payload(result):
    return {
        "flight": result.flight,
        "accommodation": result.accommodation,
        "food": result.food,
        "transport": result.transport,
        "activities": result.activities,
        "visa": result.visa,
        "insurance": result.insurance,
        "reserve": result.reserve,
    }


class TripEstimateView(APIView):
    def post(self, request):
        serializer = TripEstimateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        result = _estimate_or_404(
            destination=v["destination"],
            start_date=v["start_date"],
            duration_days=v["duration_days"],
            travelers_count=v["travelers_count"],
            style=v["style"],
        )

        return envelope(
            {
                "destination": DestinationListSerializer(v["destination"]).data,
                "duration_days": v["duration_days"],
                "travelers_count": v["travelers_count"],
                "style": v["style"],
                "confidence": result.confidence,
                "budget_min": result.budget_min,
                "budget_max": result.budget_max,
                "breakdown": _breakdown_payload(result),
            }
        )


class TripListCreateView(generics.ListCreateAPIView):
    serializer_class = TripSerializer

    def get_queryset(self):
        return (
            Trip.objects.filter(user=self.request.user)
            .select_related("destination__country", "breakdown")
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        result = _estimate_or_404(
            destination=v["destination"],
            start_date=v["start_date"],
            duration_days=v["duration_days"],
            travelers_count=v.get("travelers_count", 1),
            style=v.get("style", Trip.Style.STANDARD),
        )

        with transaction.atomic():
            trip = Trip.objects.create(
                user=request.user,
                destination=v["destination"],
                start_date=v["start_date"],
                duration_days=v["duration_days"],
                travelers_count=v.get("travelers_count", 1),
                style=v.get("style", Trip.Style.STANDARD),
                target_amount=v.get("target_amount"),
                budget_min=result.budget_min,
                budget_max=result.budget_max,
            )
            BudgetBreakdown.objects.create(trip=trip, **_breakdown_payload(result))

        return envelope(self.get_serializer(trip).data, status=201)


class TripDetailView(generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return (
            Trip.objects.filter(user=self.request.user)
            .select_related("destination__country", "breakdown")
        )

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return TripUpdateSerializer
        return TripSerializer

    def retrieve(self, request, *args, **kwargs):
        return envelope(TripSerializer(self.get_object()).data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return envelope(TripSerializer(instance).data)
