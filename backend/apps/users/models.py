from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from .managers import UserManager

phone_validator = RegexValidator(
    regex=r"^\+998\d{9}$",
    message="Telefon raqam +998901234567 formatida bo'lishi kerak",
)


class User(AbstractUser):
    class TravelStyle(models.TextChoices):
        ECONOM = "econom", "Econom"
        STANDARD = "standard", "Standard"
        COMFORT = "comfort", "Comfort"

    class Currency(models.TextChoices):
        USD = "USD", "USD"
        UZS = "UZS", "UZS"

    username = None
    email = models.EmailField(blank=True)

    phone = models.CharField(max_length=13, unique=True, validators=[phone_validator])
    full_name = models.CharField(max_length=150)
    home_city = models.CharField(max_length=50, default="Tashkent")
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.USD)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    has_passport = models.BooleanField(default=False)
    travel_style = models.CharField(max_length=10, choices=TravelStyle.choices, default=TravelStyle.STANDARD)

    notify_daily = models.BooleanField(default=True)
    notify_weekly = models.BooleanField(default=True)
    notify_streak = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    def __str__(self):
        return self.phone
