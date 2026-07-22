from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from core.responses import envelope

from .cookies import clear_auth_cookies, set_auth_cookies
from .models import TelegramLinkCode, User, VerificationCode
from .serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterRequestSerializer,
    RegisterResendSerializer,
    RegisterVerifySerializer,
    UserSerializer,
)


def _send_code_email(user, code, subject, intro):
    send_mail(
        subject=subject,
        message=(
            f"Salom {user.full_name}!\n\n"
            f"{intro}\n\n"
            f"Tasdiqlash kodingiz: {code}\n\n"
            f"Kod {VerificationCode.TTL_MINUTES} daqiqa amal qiladi.\n\n"
            f"— PolarisAI"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


class RegisterRequestView(APIView):
    """1-qadam: ma'lumotlarni qabul qiladi, emailga tasdiqlash kodi yuboradi."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        with transaction.atomic():
            User.objects.filter(phone=v["phone"], is_active=False).delete()
            User.objects.filter(email__iexact=v["email"], is_active=False).delete()
            user = User.objects.create_user(
                phone=v["phone"],
                password=v["password"],
                full_name=v["full_name"],
                email=v["email"],
                is_active=False,
            )
            code = VerificationCode.issue(user, VerificationCode.Purpose.REGISTER)

        _send_code_email(
            user,
            code.code,
            subject="PolarisAI — tasdiqlash kodi",
            intro="Ro'yxatdan o'tishni yakunlash uchun quyidagi kodni kiriting:",
        )
        return envelope(
            {"email": user.email, "detail": "Tasdiqlash kodi emailga yuborildi"},
            status=status.HTTP_201_CREATED,
        )


class RegisterResendView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterResendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email__iexact=email, is_active=False).first()
        if user is None:
            raise DRFValidationError("Bunday kutilayotgan ro'yxatdan o'tish topilmadi")

        last_code = VerificationCode.latest_for(user, VerificationCode.Purpose.REGISTER)
        if last_code:
            elapsed = (timezone.now() - last_code.created_at).total_seconds()
            if elapsed < VerificationCode.RESEND_COOLDOWN_SECONDS:
                raise DRFValidationError("Iltimos, qayta yuborishdan oldin biroz kuting")

        code = VerificationCode.issue(user, VerificationCode.Purpose.REGISTER)
        _send_code_email(
            user,
            code.code,
            subject="PolarisAI — tasdiqlash kodi",
            intro="Ro'yxatdan o'tishni yakunlash uchun quyidagi kodni kiriting:",
        )
        return envelope({"detail": "Kod qayta yuborildi"})


class RegisterVerifyView(APIView):
    """2-qadam: kodni tekshiradi, hisobni faollashtiradi va tizimga kirgizadi."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        user = User.objects.filter(email__iexact=v["email"], is_active=False).first()
        if user is None:
            raise DRFValidationError("Kod yaroqsiz yoki muddati o'tgan")

        vcode = VerificationCode.latest_for(user, VerificationCode.Purpose.REGISTER)
        if not vcode or not vcode.is_valid():
            raise DRFValidationError("Kod yaroqsiz yoki muddati o'tgan. Qayta yuborishni so'rang.")

        if vcode.code != v["code"]:
            vcode.register_wrong_attempt()
            raise DRFValidationError("Kod noto'g'ri")

        vcode.mark_used()
        user.is_active = True
        user.save(update_fields=["is_active"])

        refresh = RefreshToken.for_user(user)
        response = envelope(UserSerializer(user).data, status=status.HTTP_200_OK)
        set_auth_cookies(response, refresh.access_token, refresh)
        return response


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is not None:
            code = VerificationCode.issue(user, VerificationCode.Purpose.PASSWORD_RESET)
            _send_code_email(
                user,
                code.code,
                subject="PolarisAI — parolni tiklash kodi",
                intro=(
                    "Parolni tiklash uchun quyidagi kodni kiriting. "
                    "Agar buni siz so'ramagan bo'lsangiz, xabarni e'tiborsiz qoldiring."
                ),
            )
        return envelope({"detail": "Agar bu email ro'yxatdan o'tgan bo'lsa, tasdiqlash kodi yuborildi"})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        user = User.objects.filter(email__iexact=v["email"], is_active=True).first()
        vcode = None
        if user is not None:
            vcode = VerificationCode.latest_for(user, VerificationCode.Purpose.PASSWORD_RESET)

        if user is None or not vcode or not vcode.is_valid():
            raise DRFValidationError("Kod yaroqsiz yoki muddati o'tgan")

        if vcode.code != v["code"]:
            vcode.register_wrong_attempt()
            raise DRFValidationError("Kod noto'g'ri")

        vcode.mark_used()
        user.set_password(v["new_password"])
        user.save(update_fields=["password"])
        return envelope({"detail": "Parol muvaffaqiyatli yangilandi"})


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        response = envelope(UserSerializer(user).data)
        set_auth_cookies(response, refresh.access_token, refresh)
        return response


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        if raw_refresh is None:
            raise AuthenticationFailed("Refresh token topilmadi")

        serializer = TokenRefreshSerializer(data={"refresh": raw_refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise AuthenticationFailed("Refresh token yaroqsiz") from exc

        response = envelope({"detail": "Token yangilandi"})
        set_auth_cookies(
            response,
            serializer.validated_data["access"],
            serializer.validated_data.get("refresh"),
        )
        return response


class LogoutView(APIView):
    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        if raw_refresh:
            try:
                RefreshToken(raw_refresh).blacklist()
            except TokenError:
                pass

        response = envelope({"detail": "Chiqildi"})
        clear_auth_cookies(response)
        return response


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        return envelope(self.get_serializer(self.get_object()).data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return envelope(serializer.data)


class TelegramLinkCodeView(APIView):
    """Issues a short-lived code the user sends to the bot as
    `/start <code>` to link their Telegram account for notifications."""

    def post(self, request):
        if not settings.TELEGRAM_BOT_USERNAME:
            return envelope({"detail": "Telegram bot hali sozlanmagan"}, status=503)

        link = TelegramLinkCode.issue(request.user)
        deep_link = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={link.code}"
        return envelope(
            {
                "code": link.code,
                "bot_username": settings.TELEGRAM_BOT_USERNAME,
                "deep_link": deep_link,
                "expires_in_minutes": TelegramLinkCode.TTL_MINUTES,
            },
            status=201,
        )
