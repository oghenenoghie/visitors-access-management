from django.contrib import admin

from .models import Property, ResidentialUnit


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("name", "estate", "property_type", "parent", "status")
    list_filter = ("estate", "property_type", "status")
    search_fields = ("name", "estate__name", "estate__estate_code")


@admin.register(ResidentialUnit)
class ResidentialUnitAdmin(admin.ModelAdmin):
    list_display = ("unit_number", "property", "block", "floor", "status")
    list_filter = ("property__estate", "status")
    search_fields = ("unit_number", "block", "property__name")
