from django.contrib import admin

from .models import BudgetBreakdown, Trip


class BudgetBreakdownInline(admin.StackedInline):
    model = BudgetBreakdown
    can_delete = False


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ["user", "destination", "start_date", "duration_days", "style", "status", "created_at"]
    list_filter = ["status", "style"]
    search_fields = ["user__phone", "destination__city_uz"]
    autocomplete_fields = ["user", "destination"]
    inlines = [BudgetBreakdownInline]
