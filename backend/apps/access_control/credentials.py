import hashlib
import hmac
import secrets

from django.conf import settings


def _digest(value):
    pepper = settings.CREDENTIAL_PEPPER.encode("utf-8")
    return hmac.new(pepper, value.encode("utf-8"), hashlib.sha256).hexdigest()


def issue_secret():
    """Return opaque QR material and a human-enterable code; store only keyed hashes."""
    qr_token = secrets.token_urlsafe(32)
    access_code = f"{secrets.randbelow(100_000_000):08d}"
    return qr_token, access_code, _digest(qr_token), _digest(access_code)


def find_credential(value):
    from .models import AccessCredential

    digest = _digest(value.strip())
    return AccessCredential.objects.filter(
        models_qr_hash=digest
    ).first()


def credential_for_digest(digest):
    from .models import AccessCredential

    return AccessCredential.objects.filter(
        __import__("django").db.models.Q(qr_token_hash=digest)
        | __import__("django").db.models.Q(access_code_hash=digest)
    ).first()
