from django.db import models

from apps.trips.models import Trip


class SavingEntry(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="saving_entries")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Jamg'arish yozuvi"
        verbose_name_plural = "Jamg'arish yozuvlari"
        unique_together = [("trip", "date")]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.trip} — {self.date} — ${self.amount}"
