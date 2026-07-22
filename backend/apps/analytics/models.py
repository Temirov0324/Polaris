from django.conf import settings
from django.db import models


class AnalyticsEvent(models.Model):
    """First-party, self-hosted product-usage event log — no external
    tracking service. Anonymous events (pre-login) are correlated via
    anon_id, a random id the frontend keeps in localStorage."""

    name = models.CharField(max_length=64, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="analytics_events"
    )
    anon_id = models.CharField(max_length=64, blank=True, db_index=True)
    properties = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Analitika hodisasi"
        verbose_name_plural = "Analitika hodisalari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} @ {self.created_at:%Y-%m-%d %H:%M}"
