"""Telegram Bot API client + inbound webhook command handling.

Uses urllib instead of adding a new HTTP-client dependency -- these are
small, infrequent, fire-and-forget JSON POSTs.
"""

import json
import logging
import urllib.error
import urllib.request
from datetime import date, timedelta

from django.conf import settings

logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "Assalomu alaykum! Men PolarisAI botiman.\n\n"
    "Hisobingizni bog'lash uchun saytda Profil -> \"Telegram bilan bog'lash\" tugmasini bosing, "
    "u yerdan olingan havolani oching yoki kodni shu yerga /start <kod> shaklida yuboring.\n\n"
    "Bog'langandan so'ng kunlik eslatma, streak va narx pasayishi xabarlarini shu yerda olasiz."
)

HELP_TEXT = (
    "Buyruqlar:\n"
    "/start <kod> — hisobingizni saytdagi PolarisAI profili bilan bog'lash\n"
    "/byudjet <shahar> <kunlar> — taxminiy sayohat byudjetini hisoblash (masalan: /byudjet Dubay 5)\n"
    "/help — shu ro'yxat"
)


def send_message(chat_id, text):
    """Best-effort delivery -- a failed Telegram send must never break the
    caller (a Celery notification task, the webhook handler, etc.)."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return False

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
        return True
    except urllib.error.URLError:
        logger.exception("Telegram sendMessage failed for chat_id=%s", chat_id)
        return False


def _handle_start(chat_id, code):
    from apps.users.models import TelegramLinkCode, User

    if not code:
        send_message(chat_id, WELCOME_TEXT)
        return

    link = TelegramLinkCode.objects.filter(code=code).first()
    if not link or not link.is_valid():
        send_message(chat_id, "Kod yaroqsiz yoki muddati o'tgan. Saytdagi profilingizdan yangi kod so'rang.")
        return

    chat_id_str = str(chat_id)
    if User.objects.filter(telegram_chat_id=chat_id_str).exclude(id=link.user_id).exists():
        send_message(chat_id, "Bu Telegram hisobi allaqachon boshqa foydalanuvchiga bog'langan.")
        return

    user = link.user
    user.telegram_chat_id = chat_id_str
    user.save(update_fields=["telegram_chat_id"])
    link.mark_used()
    send_message(
        chat_id,
        f"Salom {user.full_name}! Hisobingiz muvaffaqiyatli bog'landi. Endi eslatmalarni shu yerda olasiz.",
    )


def _handle_budget(chat_id, text):
    from apps.destinations.models import Destination, PriceReference
    from apps.trips.services.budget_calculator import estimate_trip_budget

    parts = text.split()
    if len(parts) < 3:
        send_message(chat_id, "Format: /byudjet <shahar> <kunlar>\nMasalan: /byudjet Dubay 5")
        return

    city, days_str = parts[1], parts[2]
    try:
        days = int(days_str)
        if days < 1:
            raise ValueError
    except ValueError:
        send_message(chat_id, "Kunlar soni musbat butun son bo'lishi kerak. Masalan: /byudjet Dubay 5")
        return

    destination = Destination.objects.filter(city_uz__icontains=city).select_related("country").first()
    if not destination:
        send_message(chat_id, f"'{city}' topilmadi. Yo'nalishlar ro'yxati: polarisai.uz")
        return

    try:
        result = estimate_trip_budget(
            destination=destination,
            start_date=date.today() + timedelta(days=30),
            duration_days=days,
            travelers_count=1,
            style="standard",
        )
    except PriceReference.DoesNotExist:
        send_message(chat_id, f"{destination.city_uz} uchun narx ma'lumoti hali kiritilmagan.")
        return

    send_message(
        chat_id,
        f"{destination.city_uz} — {days} kun uchun taxminiy byudjet (1 kishi, standard):\n"
        f"${result.budget_min} – ${result.budget_max}\n\n"
        f"To'liq reja, jamg'arish va AI maslahat uchun: polarisai.uz",
    )


def handle_update(update: dict):
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat_id = message.get("chat", {}).get("id")
    text = (message.get("text") or "").strip()
    if chat_id is None or not text:
        return

    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        code = parts[1].strip() if len(parts) > 1 else ""
        _handle_start(chat_id, code)
    elif text.startswith("/byudjet"):
        _handle_budget(chat_id, text)
    elif text.startswith("/help"):
        send_message(chat_id, HELP_TEXT)
    else:
        send_message(chat_id, "Tushunmadim. Buyruqlar ro'yxati uchun /help yozing.")
