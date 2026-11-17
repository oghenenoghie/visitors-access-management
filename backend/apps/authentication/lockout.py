"""Failure counters per (identity, client address). Backed by the cache (Redis in production)."""

import hashlib

from django.conf import settings
from django.core.cache import cache


def _key(raw: str) -> str:
    return "lockout:" + hashlib.sha256(raw.encode()).hexdigest()


def is_locked(raw: str) -> bool:
    return cache.get(_key(raw), 0) >= settings.LOGIN_LOCKOUT["MAX_FAILURES"]


def register_failure(raw: str) -> None:
    key = _key(raw)
    window = settings.LOGIN_LOCKOUT["WINDOW_SECONDS"]
    cache.add(key, 0, timeout=window)
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=window)


def clear(raw: str) -> None:
    cache.delete(_key(raw))


def retry_after() -> int:
    return settings.LOGIN_LOCKOUT["WINDOW_SECONDS"]
