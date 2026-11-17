from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.common.scoping import EstateScopedQuerySet


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
