from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["-created_at"]
    list_display = [
        "phone",
        "full_name",
        "email",
        "home_city",
        "currency",
        "telegram_status",
        "is_active",
        "is_staff",
        "created_at",
    ]
    list_filter = ["is_active", "is_staff", "currency", "travel_style", "home_city"]
    search_fields = ["phone", "full_name", "email"]
    list_per_page = 50
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        (
            "Shaxsiy ma'lumot",
            {
                "fields": (
                    "full_name",
                    "email",
                    "home_city",
                    "currency",
                    "monthly_income",
                    "has_passport",
                    "travel_style",
                )
            },
        ),
        (
            "Bildirishnomalar",
            {"fields": ("notify_daily", "notify_weekly", "notify_streak", "notify_price_drop")},
        ),
        (
            "Telegram",
            {
                "fields": ("telegram_chat_id",),
                "description": (
                    "Foydalanuvchi Profildan bog'lagandan so'ng avtomatik to'ldiriladi — "
                    "bu yerdan qo'lda o'zgartirmang."
                ),
            },
        ),
        (
            "Ruxsatlar",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Sanalar", {"fields": ("last_login", "created_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "full_name", "password1", "password2"),
            },
        ),
    )
    readonly_fields = ["created_at", "last_login", "telegram_chat_id"]

    @admin.display(description="Telegram", boolean=True)
    def telegram_status(self, obj):
        return bool(obj.telegram_chat_id)
