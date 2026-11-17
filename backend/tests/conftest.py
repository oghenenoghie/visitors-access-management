import pytest
from rest_framework.test import APIClient

from apps.estates.models import Estate, EstateMembership, EstateRole
from apps.users.models import User

PASSWORD = "a-Long-test-passw0rd!"


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
