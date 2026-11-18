import json

import firebase_admin
from celery import shared_task
from django.conf import settings

from apps.common.crypto import decrypt

from .models import DeviceRegistration, Notification


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def deliver_push_notification(self, notification_id):
    """Deliver a persisted inbox notification to active FCM devices."""
    if not settings.FCM_ENABLED or not settings.FCM_SERVICE_ACCOUNT_JSON:
        return {"sent": 0, "disabled": True}

    from firebase_admin import credentials, messaging

    try:
        app = firebase_admin.get_app("estate-access-fcm")
    except ValueError:
        service_account = json.loads(settings.FCM_SERVICE_ACCOUNT_JSON)
        app = firebase_admin.initialize_app(
            credentials.Certificate(service_account), name="estate-access-fcm"
        )

    notification = Notification.objects.get(pk=notification_id)
    devices = DeviceRegistration.objects.filter(user=notification.user, is_active=True)
    sent = 0
    for device in devices:
        token = decrypt(device.token_encrypted)
        message = messaging.Message(
            notification=messaging.Notification(
                title=notification.title,
                body=notification.body,
            ),
            data={str(key): str(value) for key, value in notification.data.items()},
            token=token,
        )
        try:
            messaging.send(message, app=app)
            sent += 1
        except messaging.UnregisteredError:
            device.is_active = False
            device.save(update_fields=["is_active", "updated_at"])
    return {"sent": sent, "disabled": False}
