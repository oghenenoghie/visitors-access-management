"""Test settings. Uses a real PostgreSQL database: concurrency tests need row locking."""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-secret-key-not-for-production")
os.environ.setdefault("DJANGO_DEBUG", "false")
os.environ.setdefault("DATABASE_URL", "postgres://estate:estate@localhost:5432/estate_access")

from .base import *  # noqa: E402, F403

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
ALLOWED_HOSTS = ["testserver", "localhost"]
API_DOCS_ENABLED = True
CELERY_TASK_ALWAYS_EAGER = True
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
