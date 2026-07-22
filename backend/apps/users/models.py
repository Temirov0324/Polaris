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
    email = models.EmailField(blank=True, verbose_name="Elektron pochta")

    phone = models.CharField(
        max_length=13, unique=True, validators=[phone_validator], verbose_name="Telefon raqami"
    )
    full_name = models.CharField(max_length=150, verbose_name="To'liq ism")
    home_city = models.CharField(max_length=50, default="Tashkent", verbose_name="Yashash shahri")
    currency = models.CharField(
        max_length=3, choices=Currency.choices, default=Currency.USD, verbose_name="Valyuta"
    )
    monthly_income = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Oylik daromad"
    )
    has_passport = models.BooleanField(default=False, verbose_name="Pasport mavjud")
    travel_style = models.CharField(
        max_length=10, choices=TravelStyle.choices, default=TravelStyle.STANDARD, verbose_name="Sayohat uslubi"
    )

    notify_daily = models.BooleanField(default=True, verbose_name="Kunlik eslatma")
    notify_weekly = models.BooleanField(default=True, verbose_name="Haftalik hisobot")
    notify_streak = models.BooleanField(default=True, verbose_name="Streak ogohlantirishi")
    notify_price_drop = models.BooleanField(default=True, verbose_name="Narx pasayishi haqida xabar")

    # Set once the user links their account via the Telegram bot's /start
    # <code> flow. When present, notifications prefer Telegram over email
    # (see apps.notifications.tasks._notify) since open rates are far
    # higher for this user base than email.
    telegram_chat_id = models.CharField(
        max_length=32, blank=True, null=True, unique=True, verbose_name="Telegram chat ID"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ro'yxatdan o'tgan vaqti")

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return self.phone


class VerificationCode(models.Model):
    class Purpose(models.TextChoices):
        REGISTER = "register", "Ro'yxatdan o'tish"
        PASSWORD_RESET = "password_reset", "Parolni tiklash"

    MAX_ATTEMPTS = 5
    TTL_MINUTES = 10
    RESEND_COOLDOWN_SECONDS = 60

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="verification_codes", verbose_name="Foydalanuvchi"
    )
    purpose = models.CharField(max_length=20, choices=Purpose.choices, verbose_name="Maqsad")
    code = models.CharField(max_length=6, verbose_name="Kod")
    attempts = models.PositiveSmallIntegerField(default=0, verbose_name="Urinishlar soni")
    used_at = models.DateTimeField(null=True, blank=True, verbose_name="Ishlatilgan vaqti")
    expires_at = models.DateTimeField(verbose_name="Tugash vaqti")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")

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

    class Meta:
        verbose_name = "Tasdiqlash kodi"
        verbose_name_plural = "Tasdiqlash kodlari"


class TelegramLinkCode(models.Model):
    """Short-lived code a logged-in user requests from Profile and then
    sends to the bot as `/start <code>` to link their Telegram account."""

    TTL_MINUTES = 15

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="telegram_link_codes", verbose_name="Foydalanuvchi"
    )
    code = models.CharField(max_length=12, unique=True, verbose_name="Kod")
    used_at = models.DateTimeField(null=True, blank=True, verbose_name="Ishlatilgan vaqti")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")

    @classmethod
    def issue(cls, user):
        code = secrets.token_urlsafe(6).replace("_", "").replace("-", "")[:8]
        return cls.objects.create(user=user, code=code)

    def is_valid(self):
        return self.used_at is None and (timezone.now() - self.created_at).total_seconds() < self.TTL_MINUTES * 60

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])

    class Meta:
        verbose_name = "Telegram bog'lash kodi"
        verbose_name_plural = "Telegram bog'lash kodlari"
