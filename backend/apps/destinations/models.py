from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Country(models.Model):
    class VisaType(models.TextChoices):
        FREE = "free", "Vizasiz"
        ON_ARRIVAL = "on_arrival", "Chegarada beriladi"
        EVISA = "evisa", "Elektron viza"
        EMBASSY = "embassy", "Elchixona orqali"

    name_uz = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    code = models.CharField(max_length=2, unique=True)
    visa_type = models.CharField(max_length=20, choices=VisaType.choices)
    visa_cost_usd = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    visa_note_uz = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Davlat"
        verbose_name_plural = "Davlatlar"
        ordering = ["name_uz"]

    def __str__(self):
        return self.name_uz


class Destination(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="destinations")
    city_uz = models.CharField(max_length=100)
    city_en = models.CharField(max_length=100)
    image_url = models.URLField(blank=True)
    description_uz = models.TextField(blank=True)
    is_popular = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Yo'nalish"
        verbose_name_plural = "Yo'nalishlar"
        ordering = ["city_uz"]

    def __str__(self):
        return f"{self.city_uz}, {self.country.name_uz}"


class PriceReference(models.Model):
    class Confidence(models.TextChoices):
        HIGH = "high", "Yuqori"
        MEDIUM = "medium", "O'rtacha"
        LOW = "low", "Past"

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="price_references")
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])

    flight_return_usd = models.DecimalField(max_digits=8, decimal_places=2)
    hotel_night_econom = models.DecimalField(max_digits=8, decimal_places=2)
    hotel_night_standard = models.DecimalField(max_digits=8, decimal_places=2)
    hotel_night_comfort = models.DecimalField(max_digits=8, decimal_places=2)
    food_day_econom = models.DecimalField(max_digits=8, decimal_places=2)
    food_day_standard = models.DecimalField(max_digits=8, decimal_places=2)
    food_day_comfort = models.DecimalField(max_digits=8, decimal_places=2)
    transport_day_usd = models.DecimalField(max_digits=8, decimal_places=2)
    activity_day_usd = models.DecimalField(max_digits=8, decimal_places=2)

    confidence = models.CharField(max_length=10, choices=Confidence.choices, default=Confidence.MEDIUM)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Narx ma'lumotnomasi"
        verbose_name_plural = "Narx ma'lumotnomalari"
        unique_together = [("destination", "month")]
        ordering = ["destination", "month"]

    def __str__(self):
        return f"{self.destination} — {self.month}-oy"

    def hotel_night(self, style):
        return getattr(self, f"hotel_night_{style}")

    def food_day(self, style):
        return getattr(self, f"food_day_{style}")
