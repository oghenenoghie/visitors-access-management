"""Hashing and encryption helpers for stored secrets."""

import hashlib
import hmac

from cryptography.fernet import Fernet
from django.conf import settings


def hmac_digest(value: str, purpose: str) -> str:
    """Keyed hash used to store codes and tokens. ``purpose`` separates uses of the key."""
    key = f"{settings.CREDENTIAL_PEPPER}:{purpose}".encode()
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()


def _fernet() -> Fernet:
    return Fernet(settings.FIELD_ENCRYPTION_KEY.encode())


def encrypt(text: str) -> str:
    return _fernet().encrypt(text.encode()).decode()


def decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()
