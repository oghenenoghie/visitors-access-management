import hashlib
import hmac
import secrets

from django.conf import settings


def digest_secret(value):
    pepper = settings.CREDENTIAL_PEPPER.encode("utf-8")
    return hmac.new(pepper, value.encode("utf-8"), hashlib.sha256).hexdigest()


def issue_secret():
    """Return opaque QR material and a human-enterable code; store only keyed hashes."""
    qr_token = secrets.token_urlsafe(32)
    access_code = f"{secrets.randbelow(100_000_000):08d}"
    return qr_token, access_code, digest_secret(qr_token), digest_secret(access_code)
