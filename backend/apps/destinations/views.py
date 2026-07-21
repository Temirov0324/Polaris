from datetime import date

from rest_framework import generics, permissions
from rest_framework.views import APIView

from apps.trips.services.budget_calculator import estimate_trip_budget
from core.responses import envelope

from .models import Destination, PriceReference
from .serializers import (
    DestinationDetailSerializer,
    DestinationListSerializer,
    SuggestRequestSerializer,
)


class DestinationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DestinationListSerializer

    def get_queryset(self):
        qs = Destination.objects.select_related("country")
        if self.request.query_params.get("popular") == "true":
            qs = qs.filter(is_popular=True)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(city_uz__icontains=search) | qs.filter(city_en__icontains=search)
        return qs


class DestinationDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Destination.objects.select_related("country")
    serializer_class = DestinationDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        return envelope(self.get_serializer(self.get_object()).data)


class DestinationSuggestView(APIView):
    """Ranks destinations that fit inside the given budget, computed with
    the same estimator /trips/estimate/ uses (default: 1 traveler,
    standard style — the same assumptions the AI chat tool uses)."""

    def post(self, request):
        serializer = SuggestRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        start_date = date(date.today().year, v["month"], 1)
        matches = []
        for destination in Destination.objects.select_related("country"):
            try:
                result = estimate_trip_budget(
                    destination=destination,
                    start_date=start_date,
                    duration_days=v["duration_days"],
                    travelers_count=1,
                    style="standard",
                )
            except PriceReference.DoesNotExist:
                continue

            if result.budget_max <= v["budget_usd"]:
                matches.append((result.budget_max, destination, result))

        matches.sort(key=lambda item: item[0])

        data = [
            {
                **DestinationListSerializer(destination).data,
                "budget_min": result.budget_min,
                "budget_max": result.budget_max,
            }
            for _, destination, result in matches
        ]
        return envelope(data)
