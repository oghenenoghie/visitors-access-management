from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle

from apps.audit_logs import actions
from apps.audit_logs.models import AuditLog
from apps.estates.models import EstateRole

from .conftest import PASSWORD
from .helpers import login


@pytest.fixture
def resident(make_estate, make_member):
    return make_member(make_estate(), EstateRole.RESIDENT, email="res@example.com")


def test_resident_logs_in_without_two_factor(api_client, resident):
    response = login(api_client, "res@example.com", PASSWORD)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "authenticated" and body["access"] and body["refresh"]
    resident.refresh_from_db()
    assert resident.last_login is not None


def test_email_is_case_insensitive(api_client, resident):
    assert login(api_client, "RES@Example.com", PASSWORD).json()["status"] == "authenticated"


def test_me_returns_profile_and_memberships(api_client, resident):
    tokens = login(api_client, "res@example.com", PASSWORD).json()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    body = api_client.get("/api/v1/auth/me/").json()
    assert body["email"] == "res@example.com"
    assert body["two_factor_enabled"] is False
    assert [m["role"] for m in body["memberships"]] == ["resident"]
    assert "password" not in body


def test_me_requires_authentication(api_client, db):
    assert api_client.get("/api/v1/auth/me/").status_code == 401


def test_wrong_password_and_unknown_email_give_the_same_response(api_client, resident):
    bad_password = login(api_client, "res@example.com", "wrong-password-1")
    unknown = login(api_client, "nobody@example.com", "wrong-password-1")
    assert bad_password.status_code == unknown.status_code == 401
    assert bad_password.json() == unknown.json()
    assert bad_password.json()["error"]["code"] == "invalid_credentials"


def test_inactive_user_cannot_log_in_and_looks_like_bad_credentials(api_client, resident):
    resident.is_active = False
    resident.save()
    response = login(api_client, "res@example.com", PASSWORD)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_login_events_are_audited_with_ip(api_client, resident):
    login(api_client, "res@example.com", "wrong-password-1")
    login(api_client, "res@example.com", PASSWORD)
    failed = AuditLog.objects.get(action=actions.LOGIN_FAILED)
    assert failed.new_values == {"reason": "bad_password"} and failed.ip_address == "127.0.0.1"
    assert failed.estate_id == resident.memberships.get().estate_id
    assert AuditLog.objects.filter(action=actions.LOGIN_SUCCESS, actor=resident).exists()
    assert "wrong-password-1" not in str(list(AuditLog.objects.values()))


def test_account_locks_after_repeated_failures_per_client_address(api_client, resident):
    for _ in range(5):
        assert login(api_client, "res@example.com", "wrong-password-1").status_code == 401
    locked = login(api_client, "res@example.com", PASSWORD)
    assert locked.status_code == 429 and locked.json()["error"]["code"] == "throttled"
    assert AuditLog.objects.filter(action=actions.LOGIN_LOCKED).exists()
    # The real user on another address is not locked out by someone else's guessing.
    elsewhere = login(api_client, "res@example.com", PASSWORD, REMOTE_ADDR="10.9.8.7")
    assert elsewhere.status_code == 200


def test_successful_login_resets_the_failure_counter(api_client, resident):
    for _ in range(4):
        login(api_client, "res@example.com", "wrong-password-1")
    assert login(api_client, "res@example.com", PASSWORD).status_code == 200
    for _ in range(4):
        assert login(api_client, "res@example.com", "wrong-password-1").status_code == 401


def test_login_endpoint_is_rate_limited(api_client, resident, monkeypatch):
    monkeypatch.setitem(ScopedRateThrottle.THROTTLE_RATES, "login", "3/min")
    statuses = [login(api_client, "res@example.com", PASSWORD).status_code for _ in range(4)]
    assert statuses == [200, 200, 200, 429]


def test_refresh_rotates_and_old_refresh_is_rejected(api_client, resident):
    first = login(api_client, "res@example.com", PASSWORD).json()
    refreshed = api_client.post("/api/v1/auth/token/refresh/", {"refresh": first["refresh"]})
    assert refreshed.status_code == 200 and refreshed.json()["refresh"] != first["refresh"]
    replay = api_client.post("/api/v1/auth/token/refresh/", {"refresh": first["refresh"]})
    assert replay.status_code == 401


@pytest.mark.django_db(transaction=True)
def test_concurrent_refresh_requests_only_rotate_once(resident):
    """Two API workers cannot both rotate the same refresh token."""
    tokens = login(APIClient(), "res@example.com", PASSWORD).json()
    barrier = Barrier(2)

    def refresh_once():
        close_old_connections()
        try:
            client = APIClient()
            barrier.wait(timeout=10)
            response = client.post("/api/v1/auth/token/refresh/", {"refresh": tokens["refresh"]})
            body = response.json() if response.status_code == 200 else None
            return response.status_code, body
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: refresh_once(), range(2)))

    assert sorted(status for status, _ in results) == [200, 401]
    winner = next(body for status, body in results if status == 200)
    assert winner["refresh"] != tokens["refresh"]

    replay = APIClient().post("/api/v1/auth/token/refresh/", {"refresh": tokens["refresh"]})
    assert replay.status_code == 401


def test_logout_blacklists_the_refresh_token(api_client, resident):
    tokens = login(api_client, "res@example.com", PASSWORD).json()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    assert (
        api_client.post("/api/v1/auth/logout/", {"refresh": tokens["refresh"]}).status_code == 204
    )
    after = api_client.post("/api/v1/auth/token/refresh/", {"refresh": tokens["refresh"]})
    assert after.status_code == 401
    assert AuditLog.objects.filter(action=actions.LOGOUT, actor=resident).exists()


def test_logout_rejects_another_users_token_and_requires_auth(api_client, resident, make_user):
    other = make_user(email="other@example.com")
    other_tokens = login(api_client, "other@example.com", PASSWORD).json()
    mine = login(api_client, "res@example.com", PASSWORD).json()
    assert api_client.post("/api/v1/auth/logout/", {"refresh": mine["refresh"]}).status_code == 401
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {mine['access']}")
    response = api_client.post("/api/v1/auth/logout/", {"refresh": other_tokens["refresh"]})
    assert response.status_code == 400
    assert other.is_active  # untouched


def test_deactivated_account_loses_access_immediately(api_client, resident):
    tokens = login(api_client, "res@example.com", PASSWORD).json()
    resident.is_active = False
    resident.save()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    assert api_client.get("/api/v1/auth/me/").status_code == 401
    refresh = api_client.post("/api/v1/auth/token/refresh/", {"refresh": tokens["refresh"]})
    assert refresh.status_code == 401
