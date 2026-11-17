import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.authentication import totp
from apps.estates.models import Estate, EstateMembership, EstateRole
from apps.users.models import User

PASSWORD = "a-Long-test-passw0rd!"


@pytest.fixture(autouse=True)
def _clear_cache():
    """Rate limits and lockouts live in the cache; isolate every test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_user(db):
    counter = {"n": 0}

    def _make(email=None, **kwargs):
        counter["n"] += 1
        email = email or f"user{counter['n']}@example.com"
        kwargs.setdefault("first_name", "Test")
        kwargs.setdefault("last_name", "User")
        return User.objects.create_user(email=email, password=PASSWORD, **kwargs)

    return _make


@pytest.fixture
def make_estate(db):
    counter = {"n": 0}

    def _make(**kwargs):
        counter["n"] += 1
        kwargs.setdefault("name", f"Estate {counter['n']}")
        kwargs.setdefault("estate_code", f"EST{counter['n']:03d}")
        return Estate.objects.create(**kwargs)

    return _make


@pytest.fixture
def make_membership(db):
    def _make(user, estate, role=EstateRole.RESIDENT, **kwargs):
        return EstateMembership.objects.create(user=user, estate=estate, role=role, **kwargs)

    return _make


@pytest.fixture
def make_member(make_user, make_membership):
    """A user holding ``role`` in ``estate``."""

    def _make(estate, role, **user_kwargs):
        user = make_user(**user_kwargs)
        make_membership(user, estate, role)
        return user

    return _make


@pytest.fixture
def platform_admin(make_user):
    return make_user(role="super_admin")


@pytest.fixture
def clock(monkeypatch):
    """Controllable clock for TOTP. Advance ``clock.t`` by 30+ s to get a fresh time step."""

    class Clock:
        t = 1_800_000_000.0

    monkeypatch.setattr(totp, "_now", lambda: Clock.t)
    return Clock


@pytest.fixture
def auth(api_client):
    def _auth(user):
        api_client.force_authenticate(user)
        return api_client

    return _auth
