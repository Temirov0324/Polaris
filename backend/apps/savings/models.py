from django.conf import settings
from django.db import models

from apps.trips.models import Trip


class SavingEntry(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="saving_entries", verbose_name="Sayohat")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saving_entries",
        null=True,
        verbose_name="Foydalanuvchi",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Summa")
    date = models.DateField(verbose_name="Sana")
    note = models.CharField(max_length=200, blank=True, verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")

    class Meta:
        verbose_name = "Jamg'arish yozuvi"
        verbose_name_plural = "Jamg'arish yozuvlari"
        # Har bir a'zo kuniga bitta yozuv qo'sha oladi — bir xil kunga
        # qayta yuborsa, o'sha a'zoning yozuvi yangilanadi (boshqalarniki
        # emas), shu sababli user ham kalitning bir qismi.
        unique_together = [("trip", "date", "user")]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.trip} — {self.date} — ${self.amount}"
