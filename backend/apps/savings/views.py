from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.views import APIView

from apps.trips.models import Trip
from core.responses import envelope

from .models import SavingEntry
from .serializers import SavingEntrySerializer
from .services.saving_plan import calculate_streak, get_saving_plan


class SavingEntryListCreateView(generics.ListCreateAPIView):
    serializer_class = SavingEntrySerializer

    def get_trip(self):
        return get_object_or_404(Trip, pk=self.kwargs["trip_id"], user=self.request.user)

    def get_queryset(self):
        return SavingEntry.objects.filter(trip=self.get_trip())

    def create(self, request, *args, **kwargs):
        trip = self.get_trip()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        # Kuniga bitta yozuv — bir xil sanaga qayta yuborilsa, yangilanadi.
        entry, _ = SavingEntry.objects.update_or_create(
            trip=trip,
            date=v["date"],
            defaults={"amount": v["amount"], "note": v.get("note", "")},
        )
        return envelope(self.get_serializer(entry).data, status=201)


class SavingEntryDeleteView(generics.DestroyAPIView):
    def get_queryset(self):
        return SavingEntry.objects.filter(trip__user=self.request.user)


class TripPlanView(APIView):
    def get(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
        if trip.target_amount is None:
            return envelope({"detail": "Bu sayohat uchun maqsad summasi hali belgilanmagan"}, status=200)
        return envelope(get_saving_plan(trip).as_dict())


class SavingStatsView(APIView):
    def get(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
        entries = list(trip.saving_entries.all())
        entries_by_date = {entry.date: entry.amount for entry in entries}

        streak = calculate_streak(entries_by_date.keys(), today=timezone.localdate())

        today = timezone.localdate()
        weekly = [
            {
                "date": (today - timedelta(days=offset)).isoformat(),
                "amount": entries_by_date.get(today - timedelta(days=offset), 0),
            }
            for offset in range(6, -1, -1)
        ]

        return envelope({"streak": streak, "weekly": weekly})
