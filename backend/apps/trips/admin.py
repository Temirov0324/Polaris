from django.contrib import admin
from django.utils.html import format_html

from .models import BudgetBreakdown, Trip, TripMember

STATUS_COLORS = {
    Trip.Status.PLANNING: "#8f9cb3",
    Trip.Status.SAVING: "#3b82f6",
    Trip.Status.COMPLETED: "#34d399",
    Trip.Status.CANCELLED: "#f87171",
}


class BudgetBreakdownInline(admin.StackedInline):
    model = BudgetBreakdown
    can_delete = False


class TripMemberInline(admin.TabularInline):
    model = TripMember
    extra = 0
    autocomplete_fields = ["user"]
    verbose_name = "A'zo"
    verbose_name_plural = "Guruh a'zolari (egasidan tashqari)"


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "destination",
        "start_date",
        "duration_days",
        "style",
        "colored_status",
        "budget_range",
        "target_amount",
        "created_at",
    ]
    list_filter = ["status", "style", "destination__country"]
    search_fields = ["user__phone", "user__full_name", "destination__city_uz", "destination__city_en"]
    autocomplete_fields = ["user", "destination"]
    list_select_related = ["user", "destination", "destination__country"]
    date_hierarchy = "created_at"
    inlines = [BudgetBreakdownInline, TripMemberInline]

    @admin.display(description="Holat", ordering="status")
    def colored_status(self, obj):
        color = STATUS_COLORS.get(obj.status, "#8f9cb3")
        return format_html('<span style="color:{}; font-weight:600;">{}</span>', color, obj.get_status_display())

    @admin.display(description="Byudjet")
    def budget_range(self, obj):
        return f"${obj.budget_min:,.0f} – ${obj.budget_max:,.0f}"


@admin.register(TripMember)
class TripMemberAdmin(admin.ModelAdmin):
    """Standalone view mainly for search/filter across all groups — day-to-day
    editing happens via the inline on Trip."""

    list_display = ["trip", "user", "added_at"]
    search_fields = ["trip__user__phone", "trip__destination__city_uz", "user__phone", "user__full_name"]
    autocomplete_fields = ["trip", "user"]
    list_select_related = ["trip", "user", "trip__destination"]
