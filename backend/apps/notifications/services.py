from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.common.crypto import encrypt, hmac_digest

from .models import DeviceRegistration, Notification


def register_device(*, user, token, platform):
    token_hash = hmac_digest(token, "fcm-device-token")
    device, _ = DeviceRegistration.objects.update_or_create(
        token_hash=token_hash,
        defaults={
            "user": user,
            "token_encrypted": encrypt(token),
            "platform": platform,
            "is_active": True,
            "last_seen_at": timezone.now(),
        },
    )
    return device


def deactivate_device(*, user, token):
    token_hash = hmac_digest(token, "fcm-device-token")
    return DeviceRegistration.objects.filter(
        user=user, token_hash=token_hash, is_active=True
    ).update(is_active=False)


def create_notification(*, user, notification_type, title, body, data=None):
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        body=body,
        data=data or {},
    )
    if settings.FCM_ENABLED:
        from .tasks import deliver_push_notification

        transaction.on_commit(lambda: deliver_push_notification.delay(str(notification.pk)))
    return notification
