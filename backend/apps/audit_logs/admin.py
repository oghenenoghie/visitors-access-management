from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only: audit entries cannot be added, changed or deleted through the admin."""

    list_display = ("created_at", "action", "actor_email", "estate", "resource_type", "ip_address")
    list_filter = ("action",)
    search_fields = ("actor_email", "resource_id", "action")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
