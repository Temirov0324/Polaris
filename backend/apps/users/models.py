import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

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


class VerificationCode(models.Model):
    class Purpose(models.TextChoices):
        REGISTER = "register", "Ro'yxatdan o'tish"
        PASSWORD_RESET = "password_reset", "Parolni tiklash"

    MAX_ATTEMPTS = 5
    TTL_MINUTES = 10
    RESEND_COOLDOWN_SECONDS = 60

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="verification_codes")
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    code = models.CharField(max_length=6)
    attempts = models.PositiveSmallIntegerField(default=0)
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def latest_for(cls, user, purpose):
        return cls.objects.filter(user=user, purpose=purpose).order_by("-created_at").first()

    @classmethod
    def issue(cls, user, purpose):
        code = f"{secrets.randbelow(1_000_000):06d}"
        return cls.objects.create(
            user=user,
            purpose=purpose,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=cls.TTL_MINUTES),
        )

    def is_valid(self):
        return self.used_at is None and self.attempts < self.MAX_ATTEMPTS and timezone.now() < self.expires_at

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])

    def register_wrong_attempt(self):
        self.attempts += 1
        self.save(update_fields=["attempts"])
