from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
    label = "users"
    verbose_name = "Foydalanuvchilar"

    def ready(self):
        # simplejwt's token_blacklist models don't set an explicit
        # verbose_name, so Django auto-derives one from the class name —
        # that bypasses gettext entirely, so locale/uz/LC_MESSAGES can't
        # translate it. Relabel directly instead (display-only, no
        # migration needed).
        from django.apps import apps as django_apps

        try:
            outstanding = django_apps.get_model("token_blacklist", "OutstandingToken")
            outstanding._meta.verbose_name = "faol token"
            outstanding._meta.verbose_name_plural = "faol tokenlar"

            blacklisted = django_apps.get_model("token_blacklist", "BlacklistedToken")
            blacklisted._meta.verbose_name = "bloklangan token"
            blacklisted._meta.verbose_name_plural = "bloklangan tokenlar"
        except LookupError:
            pass
