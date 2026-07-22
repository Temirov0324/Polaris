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

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trips", verbose_name="Foydalanuvchi"
    )
    destination = models.ForeignKey(
        Destination, on_delete=models.PROTECT, related_name="trips", verbose_name="Yo'nalish"
    )
    start_date = models.DateField(verbose_name="Boshlanish sanasi")
    duration_days = models.PositiveIntegerField(verbose_name="Davomiyligi (kun)")
    travelers_count = models.PositiveIntegerField(default=1, verbose_name="Sayohatchilar soni")
    style = models.CharField(max_length=10, choices=Style.choices, default=Style.STANDARD, verbose_name="Uslub")

    budget_min = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Byudjet (min)")
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Byudjet (maks)")
    target_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Maqsad summasi"
    )

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PLANNING, verbose_name="Holat"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")

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

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="members", verbose_name="Sayohat")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trip_memberships",
        verbose_name="Foydalanuvchi",
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan vaqti")

    class Meta:
        verbose_name = "Sayohat a'zosi"
        verbose_name_plural = "Sayohat a'zolari"
        unique_together = [("trip", "user")]

    def __str__(self):
        return f"{self.user.phone} @ {self.trip}"


class BudgetBreakdown(models.Model):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name="breakdown", verbose_name="Sayohat")

    flight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Chipta")
    accommodation = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Turar joy")
    food = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ovqat")
    transport = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Transport")
    activities = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Faoliyatlar")
    visa = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Viza")
    insurance = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sug'urta")
    reserve = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Zaxira")

    class Meta:
        verbose_name = "Byudjet bo'linishi"
        verbose_name_plural = "Byudjet bo'linishlari"

    def __str__(self):
        return f"Breakdown — {self.trip}"
