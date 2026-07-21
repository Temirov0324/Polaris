from django.urls import path

from . import views

app_name = "destinations"

urlpatterns = [
    path("", views.DestinationListView.as_view(), name="destination-list"),
    path("suggest/", views.DestinationSuggestView.as_view(), name="destination-suggest"),
    path("<int:pk>/", views.DestinationDetailView.as_view(), name="destination-detail"),
]
