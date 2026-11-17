from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class PasswordResetCode(BaseModel):
    """Single-use recovery code issued by an administrator. Only a keyed hash is stored."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reset_codes"
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    code_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    # Set when the code is used, superseded by a newer code, or burned by failed attempts.
    consumed_at = models.DateTimeField(null=True, blank=True)
    failed_attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["user", "consumed_at"], name="auth_reset_user_consumed")]


class TotpDevice(BaseModel):
    """Authenticator-app enrolment. The secret is encrypted at rest."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="totp_device"
    )
    secret_encrypted = models.TextField()
    confirmed_at = models.DateTimeField(null=True, blank=True)
    # Last accepted 30-second time step, to reject replay of a code.
    last_used_step = models.BigIntegerField(null=True, blank=True)


class RecoveryCode(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recovery_codes"
    )
    code_hash = models.CharField(max_length=64)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "code_hash"], name="auth_recovery_user_code_unique"
            )
        ]
