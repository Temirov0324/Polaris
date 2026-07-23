from django.contrib import admin

from .models import AdminAgentLog


@admin.register(AdminAgentLog)
class AdminAgentLogAdmin(admin.ModelAdmin):
    list_display = ["tool_name", "success", "performed_by", "created_at"]
    list_filter = ["success", "tool_name"]
    search_fields = ["tool_name", "performed_by__phone"]
    list_select_related = ["performed_by"]
    date_hierarchy = "created_at"
    readonly_fields = ["performed_by", "tool_name", "arguments", "result", "success", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
