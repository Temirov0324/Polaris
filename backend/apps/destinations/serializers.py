from decimal import Decimal

from rest_framework import serializers

from .models import Country, Destination


class SuggestRequestSerializer(serializers.Serializer):
    budget_usd = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("1"))
    duration_days = serializers.IntegerField(min_value=1)
    month = serializers.IntegerField(min_value=1, max_value=12)


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name_uz", "name_en", "code", "visa_type", "visa_cost_usd", "visa_note_uz"]


class DestinationListSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name_uz", read_only=True)

    class Meta:
        model = Destination
        fields = ["id", "city_uz", "city_en", "country", "country_name", "image_url", "is_popular"]


class DestinationDetailSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)

    class Meta:
        model = Destination
        fields = ["id", "city_uz", "city_en", "country", "image_url", "description_uz", "is_popular"]
