from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["phone", "full_name", "password"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


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
