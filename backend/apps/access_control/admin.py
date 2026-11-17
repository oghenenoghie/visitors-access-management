from django.contrib import admin

from .models import AccessCredential, AccessEvent, GateDevice, Visitor, VisitorInvitation


@admin.register(GateDevice)
class GateDeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "estate", "device_identifier", "status")
    list_filter = ("estate", "status")
    search_fields = ("name", "device_identifier", "estate__name")


@admin.register(VisitorInvitation)
class VisitorInvitationAdmin(admin.ModelAdmin):
    list_display = ("visitor", "estate", "unit", "valid_from", "valid_until", "status")
    list_filter = ("estate", "status", "access_type")
    search_fields = ("visitor__full_name", "visitor__phone_number")


@admin.register(AccessEvent)
class AccessEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "status", "estate", "gate_device", "officer", "occurred_at")
    list_filter = ("estate", "event_type", "status")
    readonly_fields = [field.name for field in AccessEvent._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Visitor)
admin.site.register(AccessCredential)
