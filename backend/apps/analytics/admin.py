from django.contrib import admin

from .models import AnalyticsEvent


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "anon_id", "created_at"]
    list_filter = ["name", "created_at"]
    search_fields = ["name", "anon_id", "user__phone", "user__full_name"]
    readonly_fields = ["name", "user", "anon_id", "properties", "created_at"]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False
