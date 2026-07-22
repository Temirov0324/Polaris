from django.contrib import admin

from .models import SavingEntry


@admin.register(SavingEntry)
class SavingEntryAdmin(admin.ModelAdmin):
    list_display = ["trip", "contributor", "date", "amount", "note", "created_at"]
    list_filter = ["date"]
    search_fields = [
        "trip__user__phone",
        "trip__destination__city_uz",
        "user__phone",
        "user__full_name",
    ]
    autocomplete_fields = ["trip", "user"]
    list_select_related = ["trip", "trip__user", "trip__destination", "user"]
    date_hierarchy = "date"

    @admin.display(description="Kim qo'shdi")
    def contributor(self, obj):
        return obj.user or obj.trip.user
