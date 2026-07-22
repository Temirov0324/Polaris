from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.destinations.models import Destination


class Trip(models.Model):
    class Style(models.TextChoices):
        ECONOM = "econom", "Econom"
        STANDARD = "standard", "Standard"
        COMFORT = "comfort", "Comfort"

    class Status(models.TextChoices):
        PLANNING = "planning", "Rejalashtirilmoqda"
        SAVING = "saving", "Jamg'arilmoqda"
        COMPLETED = "completed", "Yakunlandi"
        CANCELLED = "cancelled", "Bekor qilindi"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trips")
    destination = models.ForeignKey(Destination, on_delete=models.PROTECT, related_name="trips")
    start_date = models.DateField()
    duration_days = models.PositiveIntegerField()
    travelers_count = models.PositiveIntegerField(default=1)
    style = models.CharField(max_length=10, choices=Style.choices, default=Style.STANDARD)

    budget_min = models.DecimalField(max_digits=10, decimal_places=2)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PLANNING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sayohat"
        verbose_name_plural = "Sayohatlar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.phone} — {self.destination.city_uz}"

    @staticmethod
    def visible_to(user):
        """Trips the user owns or co-funds as a TripMember — used for
        read/contribute access (savings entries, plan, stats). Editing or
        cancelling a trip is still owner-only and does NOT use this."""
        return Trip.objects.filter(Q(user=user) | Q(members__user=user)).distinct()


class TripMember(models.Model):
    """A second (or third...) person co-funding someone else's trip goal.
    The trip owner is never stored here — they're implicitly a member via
    Trip.user. Membership grants read access to the trip and the ability to
    add/see saving entries; only the owner can edit or cancel the trip
    itself."""

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trip_memberships")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sayohat a'zosi"
        verbose_name_plural = "Sayohat a'zolari"
        unique_together = [("trip", "user")]

    def __str__(self):
        return f"{self.user.phone} @ {self.trip}"


class BudgetBreakdown(models.Model):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name="breakdown")

    flight = models.DecimalField(max_digits=10, decimal_places=2)
    accommodation = models.DecimalField(max_digits=10, decimal_places=2)
    food = models.DecimalField(max_digits=10, decimal_places=2)
    transport = models.DecimalField(max_digits=10, decimal_places=2)
    activities = models.DecimalField(max_digits=10, decimal_places=2)
    visa = models.DecimalField(max_digits=10, decimal_places=2)
    insurance = models.DecimalField(max_digits=10, decimal_places=2)
    reserve = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Byudjet bo'linishi"
        verbose_name_plural = "Byudjet bo'linishlari"

    def __str__(self):
        return f"Breakdown — {self.trip}"
