from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.common.models import BaseModel
from apps.common.scoping import EstateScopedQuerySet


class Visitor(BaseModel):
    full_name = models.CharField(max_length=180)
    phone_number = models.CharField(max_length=32, blank=True)
    vehicle_registration = models.CharField(max_length=32, blank=True)

    def __str__(self):
        return self.full_name


class InvitationStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    CANCELLED = "cancelled", "Cancelled"
    COMPLETED = "completed", "Completed"


class AccessType(models.TextChoices):
    SINGLE_USE = "single_use", "Single use"
    MULTI_USE = "multi_use", "Multi use"


class VisitorInvitationQuerySet(EstateScopedQuerySet):
    estate_lookup = "estate_id"


class VisitorInvitation(BaseModel):
    visitor = models.ForeignKey(Visitor, on_delete=models.PROTECT, related_name="invitations")
    resident = models.ForeignKey(
        "residents.ResidentProfile", on_delete=models.PROTECT, related_name="invitations"
    )
    estate = models.ForeignKey(
        "estates.Estate", on_delete=models.PROTECT, related_name="visitor_invitations"
    )
    unit = models.ForeignKey(
        "properties.ResidentialUnit", on_delete=models.PROTECT, related_name="visitor_invitations"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_invitations"
    )
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    access_type = models.CharField(max_length=20, choices=AccessType.choices)
    max_uses = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=InvitationStatus.choices, default=InvitationStatus.ACTIVE
    )

    objects = VisitorInvitationQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(valid_until__gt=models.F("valid_from")),
                name="access_invitation_valid_window",
            ),
            models.CheckConstraint(
                condition=Q(max_uses__gte=1) & Q(max_uses__lte=100),
                name="access_invitation_use_limit",
            ),
        ]
        indexes = [
            models.Index(fields=["estate", "status", "valid_from"], name="access_inv_est_status"),
            models.Index(fields=["resident", "-created_at"], name="access_inv_res_created"),
        ]

    def __str__(self):
        return f"{self.visitor.full_name} — {self.estate.estate_code}"


class CredentialStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    REVOKED = "revoked", "Revoked"
    CONSUMED = "consumed", "Consumed"


class AccessCredential(BaseModel):
    invitation = models.OneToOneField(
        VisitorInvitation, on_delete=models.PROTECT, related_name="credential"
    )
    qr_token_hash = models.CharField(max_length=64, unique=True)
    access_code_hash = models.CharField(max_length=64, unique=True)
    status = models.CharField(
        max_length=20, choices=CredentialStatus.choices, default=CredentialStatus.ACTIVE
    )
    expires_at = models.DateTimeField()
    uses_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["status", "expires_at"], name="access_cred_status_exp")]

    def __str__(self):
        return f"Credential for invitation {self.invitation_id}"


class GateDeviceStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class GateDevice(BaseModel):
    estate = models.ForeignKey(
        "estates.Estate", on_delete=models.PROTECT, related_name="gate_devices"
    )
    name = models.CharField(max_length=120)
    device_identifier = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20, choices=GateDeviceStatus.choices, default=GateDeviceStatus.ACTIVE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["estate", "device_identifier"], name="access_gate_device_unique"
            )
        ]
        indexes = [models.Index(fields=["estate", "status"], name="access_gate_est_status")]

    def __str__(self):
        return f"{self.name} — {self.estate.estate_code}"


class AccessEventType(models.TextChoices):
    ENTRY = "entry", "Entry"
    EXIT = "exit", "Exit"


class AccessEventStatus(models.TextChoices):
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    OVERRIDDEN = "overridden", "Administrator override"


class ImmutableAccessEventError(Exception):
    pass


class AccessEvent(BaseModel):
    estate = models.ForeignKey(
        "estates.Estate", on_delete=models.PROTECT, related_name="access_events"
    )
    invitation = models.ForeignKey(
        VisitorInvitation, null=True, blank=True, on_delete=models.PROTECT, related_name="events"
    )
    credential = models.ForeignKey(
        AccessCredential, null=True, blank=True, on_delete=models.PROTECT, related_name="events"
    )
    gate_device = models.ForeignKey(
        GateDevice, on_delete=models.PROTECT, related_name="events"
    )
    officer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="access_events"
    )
    event_type = models.CharField(max_length=12, choices=AccessEventType.choices)
    status = models.CharField(max_length=16, choices=AccessEventStatus.choices)
    occurred_at = models.DateTimeField()
    reason = models.CharField(max_length=500, blank=True)
    related_entry = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="exit_events"
    )

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["estate", "-occurred_at"], name="access_event_est_time"),
            models.Index(
                fields=["invitation", "event_type", "status"], name="access_event_inv_type"
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(event_type="entry", related_entry__isnull=True)
                | Q(event_type="exit", related_entry__isnull=False),
                name="access_event_exit_requires_entry",
            )
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ImmutableAccessEventError("Access events cannot be modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ImmutableAccessEventError("Access events cannot be deleted.")
