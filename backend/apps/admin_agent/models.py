from django.conf import settings
from django.db import models


class AdminAgentLog(models.Model):
    """Audit trail for every tool call the content agent makes — lets the
    founder review exactly what the agent added/changed and undo by hand
    if something looks wrong. Never stores end-user personal data since the
    agent's tools (see services.tools) can't touch those models at all."""

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admin_agent_logs",
        verbose_name="Bajardi",
    )
    tool_name = models.CharField(max_length=64, verbose_name="Tool nomi")
    arguments = models.JSONField(default=dict, verbose_name="Parametrlar")
    result = models.JSONField(default=dict, verbose_name="Natija")
    success = models.BooleanField(default=True, verbose_name="Muvaffaqiyatli")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Vaqti")

    class Meta:
        verbose_name = "Agent amali"
        verbose_name_plural = "Agent amallari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tool_name} @ {self.created_at:%Y-%m-%d %H:%M}"
