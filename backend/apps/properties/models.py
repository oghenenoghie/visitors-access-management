from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import BaseModel
from apps.common.scoping import EstateScopedQuerySet


class PropertyType(models.TextChoices):
    STREET = "street", "Street"
    BLOCK = "block", "Block"
    BUILDING = "building", "Building"
    COMPOUND = "compound", "Compound"


class PropertyStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class PropertyQuerySet(EstateScopedQuerySet):
    estate_lookup = "estate_id"


class Property(BaseModel):
    """An estate location node: street, block, building or compound."""

    estate = models.ForeignKey(
        "estates.Estate", on_delete=models.PROTECT, related_name="properties"
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    name = models.CharField(max_length=160)
    property_type = models.CharField(max_length=20, choices=PropertyType.choices)
    description = models.CharField(max_length=500, blank=True)
    status = models.CharField(
        max_length=20, choices=PropertyStatus.choices, default=PropertyStatus.ACTIVE
    )

    objects = PropertyQuerySet.as_manager()

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["estate", "parent", "name"], name="properties_parent_name_unique",
                nulls_distinct=False,
            )
        ]
        indexes = [
            models.Index(
                fields=["estate", "property_type", "status"],
                name="properties_estate_type_status",
            )
        ]

    def clean(self):
        if self.parent_id and self.parent.estate_id != self.estate_id:
            raise ValidationError({"parent": "A parent property must belong to the same estate."})
        if self.parent_id == self.pk and self.pk:
            raise ValidationError({"parent": "A property cannot be its own parent."})

    def __str__(self):
        return f"{self.name} ({self.get_property_type_display()})"


class ResidentialUnitQuerySet(EstateScopedQuerySet):
    estate_lookup = "property__estate_id"


class ResidentialUnit(BaseModel):
    property = models.ForeignKey(
        Property, on_delete=models.PROTECT, related_name="residential_units"
    )
    unit_number = models.CharField(max_length=40)
    floor = models.CharField(max_length=30, blank=True)
    block = models.CharField(max_length=40, blank=True)
    status = models.CharField(
        max_length=20, choices=PropertyStatus.choices, default=PropertyStatus.ACTIVE
    )

    objects = ResidentialUnitQuerySet.as_manager()

    class Meta:
        ordering = ["property__name", "block", "unit_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["property", "block", "unit_number"], name="properties_unit_location_unique"
            )
        ]
        indexes = [models.Index(fields=["property", "status"], name="properties_unit_status")]

    def __str__(self):
        return f"{self.property.name} / {self.unit_number}"
