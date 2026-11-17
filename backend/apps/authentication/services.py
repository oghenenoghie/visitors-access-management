"""Authentication business logic. Views stay thin; every security event is audited."""

import hmac
import secrets
from datetime import timedelta
from functools import cache

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from django.core import signing
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import Throttled, ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audit_logs import actions
from apps.audit_logs.services import client_ip, record
from apps.common.crypto import hmac_digest
from apps.common.permissions import shared_administered_estate
from apps.estates.models import EstateMembership

from . import lockout, totp
from .exceptions import (
    InvalidChallenge,
    InvalidCredentials,
    InvalidResetCode,
    InvalidTwoFactorCode,
    TwoFactorState,
)
from .models import PasswordResetCode

User = get_user_model()

CHALLENGE_SALT = "estate.auth.challenge"
_RESET_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


# ----------------------------------------------------------------------------- helpers
@cache
def _dummy_hash() -> str:
    return make_password("not-a-real-password")


def requires_two_factor(user) -> bool:
    """Dashboard accounts (platform admins, estate admins and managers) need 2FA."""
    if user.is_platform_admin:
        return True
    return (
        EstateMembership.objects.active()
        .filter(user=user, role__in=settings.TWO_FACTOR["ROLES"])
        .exists()
    )


def primary_estate(user):
    """The user's only active estate, else None (used to scope audit entries)."""
    memberships = list(
        EstateMembership.objects.active().filter(user=user).select_related("estate")[:2]
    )
    return memberships[0].estate if len(memberships) == 1 else None


def issue_tokens(user) -> dict:
    refresh = RefreshToken.for_user(user)
    update_last_login(None, user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def revoke_sessions(user) -> None:
    """Blacklist every outstanding refresh token. Access tokens expire within minutes."""
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


def _make_challenge(user) -> str:
    return signing.dumps({"uid": str(user.pk), "purpose": "2fa"}, salt=CHALLENGE_SALT)


def _read_challenge(token: str):
    try:
        data = signing.loads(
            token, salt=CHALLENGE_SALT, max_age=settings.TWO_FACTOR["CHALLENGE_MAX_AGE"]
        )
    except signing.BadSignature as exc:
        raise InvalidChallenge() from exc
    user = User.objects.filter(pk=data.get("uid"), is_active=True).first()
    if user is None or data.get("purpose") != "2fa" or not requires_two_factor(user):
        raise InvalidChallenge()
    return user


def _locked(raw_key: str, request, *, actor_email: str):
    if lockout.is_locked(raw_key):
        record(action=actions.LOGIN_LOCKED, actor_email=actor_email, request=request)
        raise Throttled(wait=lockout.retry_after())


# ----------------------------------------------------------------------------- login
def login(*, email: str, password: str, request) -> dict:
    email = email.strip().lower()
    key = f"login:{email}:{client_ip(request)}"
    _locked(key, request, actor_email=email)

    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        check_password(password, _dummy_hash())  # equalise timing with a real check
        reason = "unknown_user"
    elif not user.check_password(password):
        reason = "bad_password"
    elif not user.is_active:
        reason = "inactive"
    else:
        reason = None

    if reason is not None:
        lockout.register_failure(key)
        record(
            action=actions.LOGIN_FAILED,
            actor=user,
            actor_email=email,
            estate=primary_estate(user) if user else None,
            new_values={"reason": reason},
            request=request,
        )
        raise InvalidCredentials()

    lockout.clear(key)
    if requires_two_factor(user):
        challenge = _make_challenge(user)
        state = "two_factor_required" if totp.is_enrolled(user) else "two_factor_setup_required"
        return {"status": state, "challenge_token": challenge}
    return _complete_login(user, request, method="password")


def _complete_login(user, request, *, method: str) -> dict:
    record(
        action=actions.LOGIN_SUCCESS,
        actor=user,
        estate=primary_estate(user),
        new_values={"method": method},
        request=request,
    )
    return {"status": "authenticated", **issue_tokens(user)}


# ----------------------------------------------------------------------------- 2FA
def _two_factor_key(user, request) -> str:
    return f"2fa:{user.pk}:{client_ip(request)}"


def _fail_two_factor(user, request, key, reason):
    lockout.register_failure(key)
    record(
        action=actions.TWO_FACTOR_FAILED,
        actor=user,
        estate=primary_estate(user),
        new_values={"reason": reason},
        request=request,
    )
    raise InvalidTwoFactorCode()


def start_enrolment(*, challenge_token: str, request) -> dict:
    user = _read_challenge(challenge_token)
    if totp.is_enrolled(user):
        raise TwoFactorState("Two-factor authentication is already set up.")
    secret, uri = totp.begin_enrolment(user)
    return {"secret": secret, "otpauth_uri": uri}


def confirm_enrolment(*, challenge_token: str, code: str, request) -> dict:
    user = _read_challenge(challenge_token)
    if totp.is_enrolled(user):
        raise TwoFactorState("Two-factor authentication is already set up.")
    key = _two_factor_key(user, request)
    _locked(key, request, actor_email=user.email)
    with transaction.atomic():
        recovery_codes = totp.confirm_enrolment(user, code)
        if recovery_codes is None:
            ok = False
        else:
            ok = True
            record(
                action=actions.TWO_FACTOR_ENROLLED,
                actor=user,
                estate=primary_estate(user),
                request=request,
            )
    if not ok:
        _fail_two_factor(user, request, key, "bad_enrolment_code")
    lockout.clear(key)
    result = _complete_login(user, request, method="totp")
    result["recovery_codes"] = recovery_codes
    return result


def verify_two_factor(*, challenge_token: str, code: str, request) -> dict:
    user = _read_challenge(challenge_token)
    if not totp.is_enrolled(user):
        raise TwoFactorState("Two-factor authentication has not been set up.")
    key = _two_factor_key(user, request)
    _locked(key, request, actor_email=user.email)
    if totp.verify_totp(user, code, require_confirmed=True):
        method = "totp"
    elif totp.use_recovery_code(user, code):
        method = "recovery_code"
    else:
        _fail_two_factor(user, request, key, "bad_code")
    lockout.clear(key)
    return _complete_login(user, request, method=method)


def logout(*, refresh_token: str, user, request) -> None:
    try:
        token = RefreshToken(refresh_token)
    except TokenError as exc:  # malformed, expired or already blacklisted
        raise ValidationError({"refresh": ["Invalid refresh token."]}) from exc
    if str(token.payload.get("user_id")) != str(user.pk):
        raise ValidationError({"refresh": ["Invalid refresh token."]})
    token.blacklist()
    record(action=actions.LOGOUT, actor=user, estate=primary_estate(user), request=request)


# ----------------------------------------------------------------------------- reset codes
def normalise_reset_code(code: str) -> str:
    return code.strip().upper().replace("-", "").replace(" ", "")


def _generate_reset_code() -> str:
    raw = "".join(secrets.choice(_RESET_ALPHABET) for _ in range(12))
    return f"{raw[:4]}-{raw[4:8]}-{raw[8:]}"


def issue_reset_code(*, target, actor, request):
    """Issue a single-use code for ``target``. The plaintext is returned once, never stored."""
    code = _generate_reset_code()
    now = timezone.now()
    with transaction.atomic():
        PasswordResetCode.objects.filter(user=target, consumed_at__isnull=True).update(
            consumed_at=now
        )
        reset = PasswordResetCode.objects.create(
            user=target,
            issued_by=actor,
            code_hash=hmac_digest(normalise_reset_code(code), "reset"),
            expires_at=now + timedelta(minutes=settings.PASSWORD_RESET["CODE_TTL_MINUTES"]),
        )
        record(
            action=actions.PASSWORD_RESET_ISSUED,
            actor=actor,
            estate=shared_administered_estate(actor, target),
            resource=target,
            new_values={"expires_at": reset.expires_at},
            request=request,
        )
    return code, reset.expires_at


def redeem_reset_code(*, email: str, code: str, new_password: str, request) -> None:
    email = email.strip().lower()
    key = f"reset:{email}:{client_ip(request)}"
    _locked(key, request, actor_email=email)

    user = User.objects.filter(email__iexact=email, is_active=True).first()
    outcome, weak = "invalid", None
    if user is not None:
        with transaction.atomic():
            reset = (
                PasswordResetCode.objects.select_for_update()
                .filter(user=user, consumed_at__isnull=True)
                .order_by("-created_at")
                .first()
            )
            now = timezone.now()
            if reset is not None and reset.expires_at > now:
                expected = hmac_digest(normalise_reset_code(code), "reset")
                if hmac.compare_digest(reset.code_hash, expected):
                    try:
                        validate_password(new_password, user)
                    except DjangoValidationError as exc:
                        outcome, weak = "weak", list(exc.messages)  # code is not consumed
                    else:
                        outcome = "ok"
                        reset.consumed_at = now
                        reset.save(update_fields=["consumed_at", "updated_at"])
                        user.set_password(new_password)
                        user.save(update_fields=["password", "updated_at"])
                        revoke_sessions(user)
                        record(
                            action=actions.PASSWORD_RESET_USED,
                            actor=user,
                            estate=primary_estate(user),
                            resource=user,
                            request=request,
                        )
                else:
                    reset.failed_attempts += 1
                    if reset.failed_attempts >= settings.PASSWORD_RESET["MAX_FAILED_ATTEMPTS"]:
                        reset.consumed_at = now  # too many wrong guesses: burn the code
                    reset.save(update_fields=["failed_attempts", "consumed_at", "updated_at"])

    if outcome == "ok":
        lockout.clear(key)
        return
    if outcome == "weak":
        raise ValidationError({"new_password": weak})
    lockout.register_failure(key)
    record(
        action=actions.PASSWORD_RESET_FAILED,
        actor=user,
        actor_email=email,
        estate=primary_estate(user) if user else None,
        request=request,
    )
    raise InvalidResetCode()


def reset_two_factor(*, target, actor, request) -> None:
    with transaction.atomic():
        totp.reset(target)
        revoke_sessions(target)
        record(
            action=actions.TWO_FACTOR_RESET,
            actor=actor,
            estate=shared_administered_estate(actor, target),
            resource=target,
            request=request,
        )
