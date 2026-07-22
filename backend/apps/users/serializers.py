from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User


class RegisterRequestSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    phone = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_phone(self, value):
        if User.objects.filter(phone=value, is_active=True).exists():
            raise serializers.ValidationError("Bu telefon raqam allaqachon ro'yxatdan o'tgan")
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value, is_active=True).exists():
            raise serializers.ValidationError("Bu email allaqachon ro'yxatdan o'tgan")
        return value


class RegisterResendSerializer(serializers.Serializer):
    email = serializers.EmailField()


class RegisterVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            self.context["request"],
            phone=attrs["phone"],
            password=attrs["password"],
        )
        if user is None:
            if User.objects.filter(phone=attrs["phone"], is_active=False).exists():
                raise serializers.ValidationError(
                    "Hisobingiz hali tasdiqlanmagan. Ro'yxatdan o'tishni yakunlang.",
                    code="not_verified",
                )
            raise serializers.ValidationError("Telefon raqam yoki parol noto'g'ri", code="invalid_credentials")
        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "email",
            "full_name",
            "home_city",
            "currency",
            "monthly_income",
            "has_passport",
            "travel_style",
            "notify_daily",
            "notify_weekly",
            "notify_streak",
            "created_at",
        ]
        read_only_fields = ["id", "phone", "created_at"]
