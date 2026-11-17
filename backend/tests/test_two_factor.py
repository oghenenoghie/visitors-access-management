import pytest

from apps.audit_logs import actions
from apps.audit_logs.models import AuditLog
from apps.authentication.models import RecoveryCode
from apps.common.crypto import decrypt
from apps.estates.models import EstateRole

from .conftest import PASSWORD
from .helpers import code_at, login

SETUP, CONFIRM, VERIFY = (
    "/api/v1/auth/2fa/setup/",
    "/api/v1/auth/2fa/confirm/",
    "/api/v1/auth/2fa/verify/",
)


@pytest.fixture
def manager(make_estate, make_member):
    return make_member(make_estate(), EstateRole.ESTATE_MANAGER, email="mgr@example.com")


def enrol(client, user, clock):
    """Run the full enrolment. Returns (confirm response body, challenge)."""
    challenge = login(client, user.email, PASSWORD).json()["challenge_token"]
    assert client.post(SETUP, {"challenge_token": challenge}).status_code == 200
    user.refresh_from_db()
    code = code_at(user, clock.t)
    body = client.post(CONFIRM, {"challenge_token": challenge, "code": code}).json()
    return body


def test_management_login_requires_enrolment_first(api_client, manager):
    body = login(api_client, "mgr@example.com", PASSWORD).json()
    assert body["status"] == "two_factor_setup_required"
    assert "access" not in body and body["challenge_token"]


def test_platform_admin_also_needs_two_factor(api_client, platform_admin):
    body = login(api_client, platform_admin.email, PASSWORD).json()
    assert body["status"] == "two_factor_setup_required"


def test_roles_outside_the_dashboard_do_not_need_two_factor(api_client, make_estate, make_member):
    estate = make_estate()
    for role in (EstateRole.SECURITY_OFFICER, EstateRole.RESIDENT, EstateRole.SECURITY_SUPERVISOR):
        user = make_member(estate, role)
        assert login(api_client, user.email, PASSWORD).json()["status"] == "authenticated"


def test_enrolment_issues_tokens_and_one_time_recovery_codes(api_client, manager, clock):
    challenge = login(api_client, manager.email, PASSWORD).json()["challenge_token"]
    setup = api_client.post(SETUP, {"challenge_token": challenge}).json()
    assert setup["otpauth_uri"].startswith("otpauth://totp/") and setup["secret"]
    manager.refresh_from_db()
    assert setup["secret"] not in manager.totp_device.secret_encrypted  # encrypted at rest
    assert decrypt(manager.totp_device.secret_encrypted) == setup["secret"]

    code = code_at(manager, clock.t)
    body = api_client.post(CONFIRM, {"challenge_token": challenge, "code": code}).json()
    assert body["status"] == "authenticated" and body["access"] and body["refresh"]
    assert len(body["recovery_codes"]) == 10
    assert not any(c in str(list(RecoveryCode.objects.values())) for c in body["recovery_codes"])
    assert AuditLog.objects.filter(action=actions.TWO_FACTOR_ENROLLED, actor=manager).exists()


def test_wrong_code_does_not_confirm_enrolment(api_client, manager, clock):
    challenge = login(api_client, manager.email, PASSWORD).json()["challenge_token"]
    api_client.post(SETUP, {"challenge_token": challenge})
    response = api_client.post(CONFIRM, {"challenge_token": challenge, "code": "000000"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_two_factor_code"
    manager.refresh_from_db()
    assert manager.totp_device.confirmed_at is None


def test_subsequent_login_requires_a_code(api_client, manager, clock):
    enrol(api_client, manager, clock)
    clock.t += 60
    challenge = login(api_client, manager.email, PASSWORD).json()
    assert challenge["status"] == "two_factor_required"
    ok = api_client.post(
        VERIFY, {"challenge_token": challenge["challenge_token"], "code": code_at(manager, clock.t)}
    )
    assert ok.status_code == 200 and ok.json()["status"] == "authenticated"
    assert AuditLog.objects.filter(
        action=actions.LOGIN_SUCCESS, actor=manager, new_values={"method": "totp"}
    ).exists()


def test_a_code_cannot_be_replayed(api_client, manager, clock):
    enrol(api_client, manager, clock)
    clock.t += 60
    code = code_at(manager, clock.t)
    first = login(api_client, manager.email, PASSWORD).json()["challenge_token"]
    assert api_client.post(VERIFY, {"challenge_token": first, "code": code}).status_code == 200
    second = login(api_client, manager.email, PASSWORD).json()["challenge_token"]
    assert api_client.post(VERIFY, {"challenge_token": second, "code": code}).status_code == 401


def test_wrong_code_is_rejected_and_audited(api_client, manager, clock):
    enrol(api_client, manager, clock)
    challenge = login(api_client, manager.email, PASSWORD).json()["challenge_token"]
    response = api_client.post(VERIFY, {"challenge_token": challenge, "code": "123456"})
    assert response.status_code == 401
    assert AuditLog.objects.filter(action=actions.TWO_FACTOR_FAILED, actor=manager).exists()


def test_recovery_code_works_once(api_client, manager, clock):
    codes = enrol(api_client, manager, clock)["recovery_codes"]
    first = login(api_client, manager.email, PASSWORD).json()["challenge_token"]
    ok = api_client.post(VERIFY, {"challenge_token": first, "code": codes[0].lower()})
    assert ok.status_code == 200
    second = login(api_client, manager.email, PASSWORD).json()["challenge_token"]
    assert api_client.post(VERIFY, {"challenge_token": second, "code": codes[0]}).status_code == 401
    assert api_client.post(VERIFY, {"challenge_token": second, "code": codes[1]}).status_code == 200


def test_repeated_wrong_codes_lock_the_second_step(api_client, manager, clock):
    enrol(api_client, manager, clock)
    challenge = login(api_client, manager.email, PASSWORD).json()["challenge_token"]
    for _ in range(5):
        assert (
            api_client.post(VERIFY, {"challenge_token": challenge, "code": "111111"}).status_code
            == 401
        )
    clock.t += 60
    good = api_client.post(
        VERIFY, {"challenge_token": challenge, "code": code_at(manager, clock.t)}
    )
    assert good.status_code == 429


@pytest.mark.parametrize("token", ["", "garbage", "a:b:c"])
def test_invalid_challenge_tokens_are_rejected(api_client, manager, token):
    response = api_client.post(VERIFY, {"challenge_token": token or "x", "code": "123456"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_challenge"


def test_challenge_for_a_user_without_two_factor_is_rejected(
    api_client, manager, make_user, settings
):
    from apps.authentication.services import _make_challenge

    plain = make_user()  # no memberships, not a dashboard account
    response = api_client.post(SETUP, {"challenge_token": _make_challenge(plain)})
    assert response.status_code == 401


def test_challenge_expires(api_client, manager, settings):
    challenge = login(api_client, manager.email, PASSWORD).json()["challenge_token"]
    settings.TWO_FACTOR = {**settings.TWO_FACTOR, "CHALLENGE_MAX_AGE": -1}
    response = api_client.post(SETUP, {"challenge_token": challenge})
    assert response.status_code == 401


def test_cannot_enrol_twice(api_client, manager, clock):
    enrol(api_client, manager, clock)
    challenge = login(api_client, manager.email, PASSWORD).json()["challenge_token"]
    response = api_client.post(SETUP, {"challenge_token": challenge})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "two_factor_state"


def test_platform_admin_can_reset_a_lost_authenticator(
    api_client, auth, manager, platform_admin, clock
):
    enrol(api_client, manager, clock)
    response = auth(platform_admin).post(f"/api/v1/admin/users/{manager.pk}/two-factor-reset/")
    assert response.status_code == 204
    api_client.force_authenticate(None)
    assert (
        login(api_client, manager.email, PASSWORD).json()["status"] == "two_factor_setup_required"
    )
    assert AuditLog.objects.filter(action=actions.TWO_FACTOR_RESET, actor=platform_admin).exists()


def test_estate_admin_cannot_reset_two_factor_outside_their_estate(
    auth, manager, make_estate, make_member
):
    other_admin = make_member(make_estate(), EstateRole.ESTATE_ADMIN)
    assert (
        auth(other_admin).post(f"/api/v1/admin/users/{manager.pk}/two-factor-reset/").status_code
        == 404
    )
