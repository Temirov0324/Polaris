from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Country, Destination, PriceReference


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["name_uz", "name_en", "code", "visa_type", "visa_cost_usd", "is_active"]
    list_filter = ["visa_type", "is_active"]
    search_fields = ["name_uz", "name_en", "code"]


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ["city_uz", "city_en", "country", "is_popular"]
    list_filter = ["country", "is_popular"]
    search_fields = ["city_uz", "city_en"]
    autocomplete_fields = ["country"]


class PriceReferenceResource(resources.ModelResource):
    class Meta:
        model = PriceReference
        import_id_fields = ["destination", "month"]
        fields = [
            "id",
            "destination",
            "month",
            "flight_return_usd",
            "hotel_night_econom",
            "hotel_night_standard",
            "hotel_night_comfort",
            "food_day_econom",
            "food_day_standard",
            "food_day_comfort",
            "transport_day_usd",
            "activity_day_usd",
            "confidence",
        ]


@admin.register(PriceReference)
class PriceReferenceAdmin(ImportExportModelAdmin):
    resource_classes = [PriceReferenceResource]
    list_display = ["destination", "month", "flight_return_usd", "confidence", "updated_at"]
    list_filter = ["month", "confidence"]
    search_fields = ["destination__city_uz", "destination__city_en"]
    autocomplete_fields = ["destination"]
