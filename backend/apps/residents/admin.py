from django.contrib import admin

from .models import ResidentProfile


@admin.register(ResidentProfile)
class ResidentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "estate", "status", "submitted_at", "reviewed_at", "reviewed_by")
    list_filter = ("estate", "status")
    search_fields = ("user__email", "user__first_name", "user__last_name", "estate__name")
    readonly_fields = ("submitted_at", "reviewed_at", "reviewed_by")
