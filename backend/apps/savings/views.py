from datetime import timedelta

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

from apps.trips.models import Trip, TripMember
from apps.users.models import User
from core.responses import envelope

from .models import SavingEntry
from .serializers import SavingEntrySerializer
from .services.saving_plan import calculate_streak, get_saving_plan


class SavingEntryListCreateView(generics.ListCreateAPIView):
    serializer_class = SavingEntrySerializer

    def get_trip(self):
        return get_object_or_404(Trip.visible_to(self.request.user), pk=self.kwargs["trip_id"])

    def get_queryset(self):
        return SavingEntry.objects.filter(trip=self.get_trip()).select_related("user")

    def create(self, request, *args, **kwargs):
        trip = self.get_trip()
        if trip.status not in (Trip.Status.PLANNING, Trip.Status.SAVING):
            raise ValidationError("Bu sayohat bekor qilingan yoki yakunlangan — avval uni tiklang")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        # Kuniga bitta yozuv (har bir a'zo uchun alohida) — bir xil sanaga
        # qayta yuborilsa, o'sha a'zoning yozuvi yangilanadi.
        entry, _ = SavingEntry.objects.update_or_create(
            trip=trip,
            date=v["date"],
            user=request.user,
            defaults={"amount": v["amount"], "note": v.get("note", "")},
        )
        return envelope(self.get_serializer(entry).data, status=201)


class SavingEntryDeleteView(generics.DestroyAPIView):
    def get_queryset(self):
        return SavingEntry.objects.filter(Q(user=self.request.user) | Q(trip__user=self.request.user))


class TripPlanView(APIView):
    def get(self, request, trip_id):
        trip = get_object_or_404(Trip.visible_to(request.user), pk=trip_id)
        if trip.target_amount is None:
            return envelope({"detail": "Bu sayohat uchun maqsad summasi hali belgilanmagan"}, status=200)
        return envelope(get_saving_plan(trip).as_dict())


class SavingStatsView(APIView):
    def get(self, request, trip_id):
        trip = get_object_or_404(Trip.visible_to(request.user), pk=trip_id)
        entries = list(trip.saving_entries.all())
        entries_by_date = {}
        for entry in entries:
            entries_by_date[entry.date] = entries_by_date.get(entry.date, 0) + entry.amount

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


def _member_payload(user, is_owner, contributions):
    return {
        "id": user.id,
        "full_name": user.full_name,
        "is_owner": is_owner,
        "total_saved": contributions.get(user.id, 0),
    }


class TripMembersView(APIView):
    def get(self, request, trip_id):
        trip = get_object_or_404(Trip.visible_to(request.user), pk=trip_id)
        contributions = {}
        for entry in trip.saving_entries.select_related("user"):
            key = entry.user_id or trip.user_id
            contributions[key] = contributions.get(key, 0) + entry.amount

        data = [_member_payload(trip.user, True, contributions)]
        data += [_member_payload(m.user, False, contributions) for m in trip.members.select_related("user")]
        return envelope(data)

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
        phone = (request.data.get("phone") or "").strip()

        target = User.objects.filter(phone=phone, is_active=True).first()
        if target is None:
            return envelope({"detail": "Bu telefon raqam bilan foydalanuvchi topilmadi"}, status=404)
        if target.id == trip.user_id:
            return envelope({"detail": "Bu sayohatning egasi allaqachon siz"}, status=400)

        _, created = TripMember.objects.get_or_create(trip=trip, user=target)
        if not created:
            return envelope({"detail": "Bu foydalanuvchi allaqachon a'zo"}, status=400)

        return envelope(_member_payload(target, False, {}), status=201)


class TripMemberRemoveView(APIView):
    def delete(self, request, trip_id, user_id):
        trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
        deleted, _ = TripMember.objects.filter(trip=trip, user_id=user_id).delete()
        if not deleted:
            return envelope({"detail": "A'zo topilmadi"}, status=404)
        return envelope({"detail": "A'zo o'chirildi"})
