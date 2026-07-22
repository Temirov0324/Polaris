from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Country(models.Model):
    class VisaType(models.TextChoices):
        FREE = "free", "Vizasiz"
        ON_ARRIVAL = "on_arrival", "Chegarada beriladi"
        EVISA = "evisa", "Elektron viza"
        EMBASSY = "embassy", "Elchixona orqali"

    name_uz = models.CharField(max_length=100, verbose_name="Nomi (o'zbekcha)")
    name_en = models.CharField(max_length=100, verbose_name="Nomi (inglizcha)")
    code = models.CharField(max_length=2, unique=True, verbose_name="Kod")
    visa_type = models.CharField(max_length=20, choices=VisaType.choices, verbose_name="Viza turi")
    visa_cost_usd = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="Viza narxi (USD)")
    visa_note_uz = models.TextField(blank=True, verbose_name="Viza haqida izoh")
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        verbose_name = "Davlat"
        verbose_name_plural = "Davlatlar"
        ordering = ["name_uz"]

    def __str__(self):
        return self.name_uz


class Destination(models.Model):
    country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name="destinations", verbose_name="Davlat"
    )
    city_uz = models.CharField(max_length=100, verbose_name="Shahar (o'zbekcha)")
    city_en = models.CharField(max_length=100, verbose_name="Shahar (inglizcha)")
    image_url = models.URLField(blank=True, verbose_name="Rasm havolasi")
    description_uz = models.TextField(blank=True, verbose_name="Tavsif")
    is_popular = models.BooleanField(default=False, verbose_name="Mashhur")

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

    destination = models.ForeignKey(
        Destination, on_delete=models.CASCADE, related_name="price_references", verbose_name="Yo'nalish"
    )
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], verbose_name="Oy")

    flight_return_usd = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="Chipta narxi (borish-kelish, USD)"
    )
    hotel_night_econom = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="Mehmonxona/kecha (econom)"
    )
    hotel_night_standard = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="Mehmonxona/kecha (standard)"
    )
    hotel_night_comfort = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="Mehmonxona/kecha (comfort)"
    )
    food_day_econom = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Ovqat/kun (econom)")
    food_day_standard = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Ovqat/kun (standard)")
    food_day_comfort = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Ovqat/kun (comfort)")
    transport_day_usd = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Transport/kun (USD)")
    activity_day_usd = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Faoliyat/kun (USD)")

    confidence = models.CharField(
        max_length=10, choices=Confidence.choices, default=Confidence.MEDIUM, verbose_name="Ishonchlilik"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqti")

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
