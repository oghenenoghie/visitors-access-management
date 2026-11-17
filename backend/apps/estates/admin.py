from django.contrib import admin

from .models import Estate, EstateMembership


@admin.register(Estate)
class EstateAdmin(admin.ModelAdmin):
    list_display = ("name", "estate_code", "status", "timezone")
    list_filter = ("status",)
    search_fields = ("name", "estate_code")


@admin.register(EstateMembership)
class EstateMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "estate", "role", "status")
    list_filter = ("role", "status", "estate")
    search_fields = ("user__email", "estate__name", "estate__estate_code")
    autocomplete_fields = ("user", "estate")
