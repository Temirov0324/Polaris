from django.contrib import admin
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Country, Destination, PriceReference


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["name_uz", "name_en", "code", "visa_type", "visa_cost_usd", "is_active"]
    list_editable = ["is_active"]
    list_filter = ["visa_type", "is_active"]
    search_fields = ["name_uz", "name_en", "code"]


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ["thumbnail", "city_uz", "city_en", "country", "is_popular", "price_months"]
    list_display_links = ["city_uz"]
    list_editable = ["is_popular"]
    list_filter = ["country", "is_popular"]
    search_fields = ["city_uz", "city_en"]
    autocomplete_fields = ["country"]
    list_select_related = ["country"]

    @admin.display(description="Rasm")
    def thumbnail(self, obj):
        if not obj.image_url:
            return "—"
        return format_html(
            '<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:4px;" />', obj.image_url
        )

    @admin.display(description="Narx ma'lumoti bor oylar")
    def price_months(self, obj):
        months = sorted(obj.price_references.values_list("month", flat=True))
        if not months:
            return format_html('<span style="color:#f87171;">yo\'q</span>')
        if len(months) == 12:
            return "12/12"
        return f"{len(months)}/12"


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
    list_editable = ["confidence"]
    list_display_links = ["destination"]
    list_filter = ["month", "confidence"]
    search_fields = ["destination__city_uz", "destination__city_en"]
    autocomplete_fields = ["destination"]
    list_select_related = ["destination"]
