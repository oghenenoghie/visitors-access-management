from rest_framework import serializers

from .models import DevicePlatform, Notification


class DeviceRegistrationSerializer(serializers.Serializer):
    token = serializers.CharField(min_length=20, max_length=4096, trim_whitespace=True)
    platform = serializers.ChoiceField(choices=DevicePlatform.choices)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "notification_type", "title", "body", "data", "read_at", "created_at"]
        read_only_fields = fields
