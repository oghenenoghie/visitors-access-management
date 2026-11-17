import ipaddress
import json

from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.throttling import BaseThrottle

from .models import AuditLog

# Values under these keys are never written to the audit log.
REDACTED_KEYS = {
    "password",
    "new_password",
    "secret",
    "token",
    "access",
    "refresh",
    "code",
    "recovery_codes",
    "challenge_token",
    "code_hash",
    "secret_encrypted",
}


def _clean(values):
    if values is None:
        return None
    redacted = {
        key: ("[redacted]" if key.lower() in REDACTED_KEYS else value)
        for key, value in dict(values).items()
    }
    return json.loads(json.dumps(redacted, cls=DjangoJSONEncoder))


def client_ip(request):
    """Client address using the same trust rules as rate limiting (settings NUM_PROXIES)."""
    if request is None:
        return None
    ident = BaseThrottle().get_ident(request)
    try:
        return str(ipaddress.ip_address(ident))
    except ValueError:
        return None


def record(
    *,
    action,
    actor=None,
    actor_email="",
    estate=None,
    resource=None,
    resource_type="",
    resource_id="",
    previous_values=None,
    new_values=None,
    request=None,
):
    if resource is not None:
        resource_type = resource_type or resource._meta.label_lower
        resource_id = resource_id or str(resource.pk)
    if actor is not None and not getattr(actor, "is_authenticated", False):
        actor = None
    return AuditLog.objects.create(
        action=action,
        actor=actor,
        actor_email=(actor.email if actor is not None else actor_email)[:254],
        estate=estate,
        resource_type=resource_type,
        resource_id=resource_id,
        previous_values=_clean(previous_values),
        new_values=_clean(new_values),
        ip_address=client_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT", "")[:300] if request else ""),
    )
