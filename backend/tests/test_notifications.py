import pytest
from django.utils import timezone
from rest_framework import status

from apps.common.crypto import decrypt
from apps.notifications.models import DeviceRegistration, Notification

pytestmark = pytest.mark.django_db

API = "/api/v1/"


def test_authenticated_user_can_register_and_unregister_push_device(api_client, make_user):
    user = make_user()
    api_client.force_authenticate(user)
    token = "fcm-device-token-" + ("x" * 80)

    response = api_client.post(
        API + "devices/push-token/",
        {"token": token, "platform": "android"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"registered": True}
    device = DeviceRegistration.objects.get(user=user)
    assert device.token_encrypted != token
    assert decrypt(device.token_encrypted) == token
    assert device.token_hash != token

    response = api_client.delete(
        API + "devices/push-token/",
        {"token": token, "platform": "android"},
        format="json",
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    device.refresh_from_db()
    assert device.is_active is False


def test_registering_same_token_moves_device_to_current_account(api_client, make_user):
    first_user = make_user()
    second_user = make_user()
    token = "fcm-device-token-" + ("y" * 80)

    api_client.force_authenticate(first_user)
    api_client.post(API + "devices/push-token/", {"token": token, "platform": "android"}, format="json")
    api_client.force_authenticate(second_user)
    response = api_client.post(
        API + "devices/push-token/", {"token": token, "platform": "ios"}, format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    assert DeviceRegistration.objects.count() == 1
    device = DeviceRegistration.objects.get()
    assert device.user == second_user
    assert device.platform == "ios"


def test_notification_inbox_is_private_and_can_mark_read(api_client, make_user):
    owner = make_user()
    other = make_user()
    notification = Notification.objects.create(
        user=owner,
        notification_type="visitor.checked_in",
        title="Visitor arrived",
        body="Your visitor has entered the estate.",
        data={"event_id": "evt_123"},
    )
    api_client.force_authenticate(other)
    response = api_client.get(API + "notifications/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 0
    assert api_client.post(API + f"notifications/{notification.pk}/read/").status_code == 404

    api_client.force_authenticate(owner)
    response = api_client.get(API + "notifications/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(notification.pk)

    response = api_client.post(API + f"notifications/{notification.pk}/read/")
    assert response.status_code == status.HTTP_200_OK
    notification.refresh_from_db()
    assert notification.read_at is not None
    assert notification.read_at <= timezone.now()


def test_push_device_registration_requires_authentication(api_client):
    response = api_client.post(
        API + "devices/push-token/",
        {"token": "fcm-device-token-" + ("z" * 80), "platform": "android"},
        format="json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
