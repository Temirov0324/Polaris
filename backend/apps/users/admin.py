from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["-created_at"]
    list_display = ["phone", "full_name", "home_city", "travel_style", "is_staff", "created_at"]
    search_fields = ["phone", "full_name"]
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
            {"fields": ("notify_daily", "notify_weekly", "notify_streak")},
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
    readonly_fields = ["created_at", "last_login"]
