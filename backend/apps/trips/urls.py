from django.urls import path

from . import views

app_name = "trips"

urlpatterns = [
    path("trips/estimate/", views.TripEstimateView.as_view(), name="trip-estimate"),
    path("trips/", views.TripListCreateView.as_view(), name="trip-list"),
    path("trips/<int:pk>/", views.TripDetailView.as_view(), name="trip-detail"),
    # GET trips/{id}/plan/ is added in phase 4 alongside the saving_plan service.
]
