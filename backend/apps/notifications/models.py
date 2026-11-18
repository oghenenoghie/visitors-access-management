from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class DevicePlatform(models.TextChoices):
    ANDROID = "android", "Android"
    IOS = "ios", "iOS"


class DeviceRegistration(BaseModel):
    """A user's push endpoint. The raw FCM token is encrypted, never exposed by the API."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_devices"
    )
    token_hash = models.CharField(max_length=64, unique=True)
    token_encrypted = models.TextField()
    platform = models.CharField(max_length=12, choices=DevicePlatform.choices)
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField()

    class Meta:
        indexes = [models.Index(fields=["user", "is_active"], name="notif_device_user_active")]


class Notification(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(max_length=64)
    title = models.CharField(max_length=160)
    body = models.CharField(max_length=500)
    data = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"], name="notif_user_created")]
