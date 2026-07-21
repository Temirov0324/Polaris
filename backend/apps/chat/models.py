from django.conf import settings
from django.db import models

from apps.trips.models import Trip


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "Foydalanuvchi"
        ASSISTANT = "assistant", "Yordamchi"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_messages")
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, blank=True, related_name="chat_messages")
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Chat xabari"
        verbose_name_plural = "Chat xabarlari"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:40]}"
