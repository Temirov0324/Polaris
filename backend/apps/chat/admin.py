from django.contrib import admin

from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "short_content", "created_at"]
    list_filter = ["role"]
    search_fields = ["user__phone", "user__full_name", "content"]
    list_select_related = ["user"]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Xabar")
    def short_content(self, obj):
        return obj.content[:60]
