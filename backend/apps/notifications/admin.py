from django.contrib import admin

from .models import DeviceRegistration, Notification


@admin.register(DeviceRegistration)
class DeviceRegistrationAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "is_active", "last_seen_at")
    list_filter = ("platform", "is_active")
    search_fields = ("user__email", "token_hash")
    readonly_fields = ("token_hash", "token_encrypted", "last_seen_at")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "notification_type", "title", "read_at", "created_at")
    list_filter = ("notification_type",)
    search_fields = ("user__email", "title", "body")
    readonly_fields = (
        "user",
        "notification_type",
        "title",
        "body",
        "data",
        "read_at",
        "created_at",
        "updated_at",
    )
