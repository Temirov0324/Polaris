from django.urls import path

from . import views

app_name = "savings"

urlpatterns = [
    path("trips/<int:trip_id>/plan/", views.TripPlanView.as_view(), name="trip-plan"),
    path("trips/<int:trip_id>/savings/", views.SavingEntryListCreateView.as_view(), name="saving-list"),
    path("trips/<int:trip_id>/savings/stats/", views.SavingStatsView.as_view(), name="saving-stats"),
    path("savings/<int:pk>/", views.SavingEntryDeleteView.as_view(), name="saving-delete"),
]
