from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from django.db.models import Q

from apps.common.models import BaseModel
from apps.common.scoping import EstateScopedQuerySet
from apps.properties.models import ResidentialUnit


class ResidentStatus(models.TextChoices):
    PENDING = "pending", "Pending approval"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    SUSPENDED = "suspended", "Suspended"


class ResidentQuerySet(EstateScopedQuerySet):
    estate_lookup = "estate_id"


class ResidentProfile(BaseModel):
    """Estate-specific resident identity; pending residents have no active membership."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="resident_profiles"
    )
    estate = models.ForeignKey(
        "estates.Estate", on_delete=models.PROTECT, related_name="resident_profiles"
    )
    status = models.CharField(
        max_length=20, choices=ResidentStatus.choices, default=ResidentStatus.PENDING
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_resident_profiles",
    )
    review_note = models.CharField(max_length=500, blank=True)

    objects = ResidentQuerySet.as_manager()

    class Meta:
        ordering = ["-submitted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "estate"], name="residents_user_estate_unique"
            )
        ]
        indexes = [
            models.Index(fields=["estate", "status"], name="residents_estate_status"),
            models.Index(fields=["user", "status"], name="residents_user_status"),
        ]

    def __str__(self):
        return f"{self.user.email} — {self.estate.estate_code} ({self.status})"


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


class ResidentDocumentType(models.TextChoices):
    NATIONAL_ID = "national_id", "National identity card"
    PASSPORT = "passport", "Passport"
    DRIVERS_LICENSE = "drivers_license", "Driver's licence"
    OTHER = "other", "Other approved identity document"


class ResidentDocumentStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"


class ResidentIdentityDocument(BaseModel):
    resident = models.ForeignKey(
        ResidentProfile, on_delete=models.PROTECT, related_name="identity_documents"
    )
    document_type = models.CharField(max_length=24, choices=ResidentDocumentType.choices)
    status = models.CharField(
        max_length=20, choices=ResidentDocumentStatus.choices, default=ResidentDocumentStatus.ACTIVE
    )
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size_bytes = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    storage_key = models.CharField(max_length=500)
    wrapped_data_key = models.TextField()
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_resident_documents",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["resident", "status"], name="resident_docs_status"),
        ]

    def __str__(self):
        return f"{self.get_document_type_display()} — {self.resident.user.email}"
