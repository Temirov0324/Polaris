from django.contrib import admin

from .models import SavingEntry


@admin.register(SavingEntry)
class SavingEntryAdmin(admin.ModelAdmin):
    list_display = ["trip", "date", "amount", "created_at"]
    list_filter = ["date"]
    search_fields = ["trip__user__phone", "trip__destination__city_uz"]
    autocomplete_fields = ["trip"]
