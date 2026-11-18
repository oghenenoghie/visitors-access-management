from django.urls import path

from .views import (
    DeviceRegistrationView,
    NotificationListView,
    NotificationReadView,
    NotificationUnreadCountView,
)

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path(
        "notifications/unread-count/",
        NotificationUnreadCountView.as_view(),
        name="notification-unread-count",
    ),
    path("notifications/<uuid:pk>/read/", NotificationReadView.as_view(), name="notification-read"),
    path("devices/push-token/", DeviceRegistrationView.as_view(), name="push-device-registration"),
]
