from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from apps.common.models import BaseModel
from apps.common.scoping import EstateScopedQuerySet


def validate_timezone(value):
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError, KeyError) as exc:
        raise ValidationError("Enter a valid IANA timezone, e.g. Africa/Lagos.") from exc


estate_code_validator = RegexValidator(
    r"^[A-Z0-9][A-Z0-9_-]{1,31}$",
    "Use 2-32 characters: capitals, digits, hyphen or underscore.",
)


class EstateStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    INACTIVE = "inactive", "Inactive"


class EstateRole(models.TextChoices):
    ESTATE_ADMIN = "estate_admin", "Estate administrator"
    ESTATE_MANAGER = "estate_manager", "Estate manager"
    RESIDENT = "resident", "Resident"
    HOUSEHOLD_MEMBER = "household_member", "Household member"
    SECURITY_SUPERVISOR = "security_supervisor", "Security supervisor"
    SECURITY_OFFICER = "security_officer", "Security officer"


class MembershipStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    ENDED = "ended", "Ended"


class EstateQuerySet(EstateScopedQuerySet):
    estate_lookup = "id"


class Estate(BaseModel):
    name = models.CharField(max_length=200)
    estate_code = models.CharField(max_length=32, unique=True, validators=[estate_code_validator])
    address = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=32, blank=True)
    timezone = models.CharField(
        max_length=64, default="Africa/Lagos", validators=[validate_timezone]
    )
    status = models.CharField(
        max_length=20, choices=EstateStatus.choices, default=EstateStatus.ACTIVE
    )

    objects = EstateQuerySet.as_manager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.estate_code})"


class EstateMembershipQuerySet(EstateScopedQuerySet):
    def active(self):
        return self.filter(status=MembershipStatus.ACTIVE, estate__status=EstateStatus.ACTIVE)


class EstateMembership(BaseModel):
    """A user's role in one estate. Roles are estate-scoped; platform admins are separate."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    estate = models.ForeignKey(Estate, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=30, choices=EstateRole.choices)
    status = models.CharField(
        max_length=20, choices=MembershipStatus.choices, default=MembershipStatus.ACTIVE
    )

    objects = EstateMembershipQuerySet.as_manager()

    class Meta:
        ordering = ["estate__name", "user__email"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "estate"], name="estates_membership_user_estate_unique"
            ),
        ]
        indexes = [models.Index(fields=["estate", "role"], name="estates_member_estate_role")]

    def __str__(self):
        return f"{self.user} - {self.role} @ {self.estate.estate_code}"
