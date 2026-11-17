from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from django.db.models import Q

from apps.common.models import BaseModel
from apps.properties.models import ResidentialUnit

from .models import ResidentProfile


class AssignmentStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ENDED = "ended", "Ended"


class AssignmentRelationship(models.TextChoices):
    OWNER = "owner", "Owner"
    TENANT = "tenant", "Tenant"
    OCCUPANT = "occupant", "Occupant"


class ResidentUnitAssignment(BaseModel):
    resident = models.ForeignKey(
        ResidentProfile, on_delete=models.PROTECT, related_name="unit_assignments"
    )
    unit = models.ForeignKey(
        ResidentialUnit, on_delete=models.PROTECT, related_name="resident_assignments"
    )
    relationship = models.CharField(max_length=20, choices=AssignmentRelationship.choices)
    status = models.CharField(
        max_length=20, choices=AssignmentStatus.choices, default=AssignmentStatus.ACTIVE
    )
    is_primary = models.BooleanField(default=False)
    starts_on = models.DateField()
    ends_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-starts_on", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(ends_on__isnull=True) | Q(ends_on__gte=models.F("starts_on")),
                name="residents_assignment_valid_dates",
            ),
            models.UniqueConstraint(
                fields=["resident"],
                condition=Q(status=AssignmentStatus.ACTIVE, is_primary=True),
                name="residents_one_active_primary_unit",
            ),
        ]
        indexes = [
            models.Index(fields=["resident", "status"], name="residents_assignment_status"),
            models.Index(fields=["unit", "status"], name="units_assignment_status"),
        ]

    def clean(self):
        if self.resident_id and self.unit_id:
            if self.resident.estate_id != self.unit.property.estate_id:
                raise DjangoValidationError(
                    {"unit": "The assigned unit must belong to the resident's estate."}
                )
        if self.ends_on and self.ends_on < self.starts_on:
            raise DjangoValidationError({"ends_on": "End date cannot precede start date."})

    def __str__(self):
        return f"{self.resident.user.email} → {self.unit}"
