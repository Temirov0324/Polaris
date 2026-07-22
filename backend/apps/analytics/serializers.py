from rest_framework import serializers


class TrackEventSerializer(serializers.Serializer):
    event = serializers.CharField(max_length=64)
    anon_id = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    properties = serializers.DictField(required=False, default=dict)
