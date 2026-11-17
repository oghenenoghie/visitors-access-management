"""Authenticator-app (TOTP) enrolment and verification, plus recovery codes."""

import hmac
import secrets
import time

import pyotp
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.common.crypto import decrypt, encrypt, hmac_digest

from .models import RecoveryCode, TotpDevice

STEP_SECONDS = 30
RECOVERY_CODE_COUNT = 10
_RECOVERY_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _now() -> float:
    return time.time()


def is_enrolled(user) -> bool:
    return TotpDevice.objects.filter(user=user, confirmed_at__isnull=False).exists()


def begin_enrolment(user):
    """Create or replace an unconfirmed device. Returns (secret, otpauth_uri)."""
    secret = pyotp.random_base32()
    TotpDevice.objects.update_or_create(
        user=user,
        confirmed_at__isnull=True,
        defaults={"secret_encrypted": encrypt(secret), "last_used_step": None},
    )
    uri = pyotp.TOTP(secret).provisioning_uri(
        name=user.email, issuer_name=settings.TWO_FACTOR["ISSUER"]
    )
    return secret, uri


def _matching_step(secret: str, code: str):
    """The 30-second step ``code`` is valid for (previous, current or next), else None."""
    if not (code.isdigit() and len(code) == 6):
        return None
    totp = pyotp.TOTP(secret)
    current = int(_now() // STEP_SECONDS)
    for step in (current - 1, current, current + 1):
        if hmac.compare_digest(totp.at(step * STEP_SECONDS), code):
            return step
    return None


def verify_totp(user, code: str, *, require_confirmed: bool) -> bool:
    """Check a code and record its time step so it cannot be replayed."""
    code = code.strip().replace(" ", "")
    with transaction.atomic():
        device = TotpDevice.objects.select_for_update().filter(user=user).first()
        if device is None or (require_confirmed and device.confirmed_at is None):
            return False
        step = _matching_step(decrypt(device.secret_encrypted), code)
        if step is None:
            return False
        if device.last_used_step is not None and step <= device.last_used_step:
            return False
        device.last_used_step = step
        device.save(update_fields=["last_used_step", "updated_at"])
        return True


def normalise_recovery_code(code: str) -> str:
    return code.strip().upper().replace("-", "").replace(" ", "")


def _new_recovery_code() -> str:
    raw = "".join(secrets.choice(_RECOVERY_ALPHABET) for _ in range(10))
    return f"{raw[:5]}-{raw[5:]}"


def confirm_enrolment(user, code: str):
    """Confirm the pending device with a valid code. Returns recovery codes, or None."""
    with transaction.atomic():
        if not verify_totp(user, code, require_confirmed=False):
            return None
        TotpDevice.objects.filter(user=user).update(confirmed_at=timezone.now())
        RecoveryCode.objects.filter(user=user).delete()
        codes = [_new_recovery_code() for _ in range(RECOVERY_CODE_COUNT)]
        RecoveryCode.objects.bulk_create(
            RecoveryCode(
                user=user,
                code_hash=hmac_digest(normalise_recovery_code(c), "recovery"),
            )
            for c in codes
        )
        return codes


def use_recovery_code(user, code: str) -> bool:
    digest = hmac_digest(normalise_recovery_code(code), "recovery")
    updated = RecoveryCode.objects.filter(user=user, code_hash=digest, used_at__isnull=True).update(
        used_at=timezone.now()
    )
    return updated == 1


def reset(user) -> None:
    """Remove the user's 2FA enrolment (lost authenticator). They must enrol again."""
    TotpDevice.objects.filter(user=user).delete()
    RecoveryCode.objects.filter(user=user).delete()
