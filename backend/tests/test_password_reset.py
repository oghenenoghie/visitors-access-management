from datetime import timedelta

import pytest
from django.utils import timezone

from apps.audit_logs import actions
from apps.audit_logs.models import AuditLog
from apps.authentication.models import PasswordResetCode
from apps.estates.models import EstateRole

from .conftest import PASSWORD
from .helpers import login

REDEEM = "/api/v1/auth/password/reset/"
NEW = "a-Different-passw0rd!"


def issue_url(user):
    return f"/api/v1/admin/users/{user.pk}/password-reset/"


@pytest.fixture
def setup(make_estate, make_member):
    estate = make_estate()
    return {
        "estate": estate,
        "admin": make_member(estate, EstateRole.ESTATE_ADMIN),
        "resident": make_member(estate, EstateRole.RESIDENT, email="res@example.com"),
    }


def redeem(client, email, code, password=NEW):
    return client.post(REDEEM, {"email": email, "code": code, "new_password": password})


def test_estate_admin_issues_a_code_and_the_user_resets_their_password(api_client, auth, setup):
    issued = auth(setup["admin"]).post(issue_url(setup["resident"]))
    assert issued.status_code == 201
    code = issued.json()["code"]
    assert len(code.replace("-", "")) == 12
    api_client.force_authenticate(None)
    assert redeem(api_client, "res@example.com", code).status_code == 204
    assert login(api_client, "res@example.com", NEW).status_code == 200
    assert login(api_client, "res@example.com", PASSWORD).status_code == 401


def test_code_is_stored_only_as_a_hash(auth, setup):
    code = auth(setup["admin"]).post(issue_url(setup["resident"])).json()["code"]
    stored = PasswordResetCode.objects.get(user=setup["resident"])
    assert code not in stored.code_hash and code.replace("-", "") not in stored.code_hash
    assert code not in str(list(AuditLog.objects.values()))


def test_code_is_single_use(api_client, auth, setup):
    code = auth(setup["admin"]).post(issue_url(setup["resident"])).json()["code"]
    api_client.force_authenticate(None)
    assert redeem(api_client, "res@example.com", code).status_code == 204
    again = redeem(api_client, "res@example.com", code, "yet-Another-passw0rd")
    assert again.status_code == 400 and again.json()["error"]["code"] == "invalid_reset_code"


def test_code_format_is_forgiving(api_client, auth, setup):
    code = auth(setup["admin"]).post(issue_url(setup["resident"])).json()["code"]
    api_client.force_authenticate(None)
    assert redeem(api_client, "RES@example.com", code.lower().replace("-", " ")).status_code == 204


def test_a_new_code_supersedes_the_previous_one(api_client, auth, setup):
    client = auth(setup["admin"])
    first = client.post(issue_url(setup["resident"])).json()["code"]
    second = client.post(issue_url(setup["resident"])).json()["code"]
    client.force_authenticate(None)
    assert redeem(client, "res@example.com", first).status_code == 400
    assert redeem(client, "res@example.com", second).status_code == 204


def test_expired_code_is_rejected(api_client, auth, setup):
    code = auth(setup["admin"]).post(issue_url(setup["resident"])).json()["code"]
    PasswordResetCode.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    api_client.force_authenticate(None)
    assert redeem(api_client, "res@example.com", code).status_code == 400


def test_wrong_codes_burn_the_code_after_five_attempts(api_client, auth, setup, settings):
    code = auth(setup["admin"]).post(issue_url(setup["resident"])).json()["code"]
    api_client.force_authenticate(None)
    for i in range(5):
        response = redeem(api_client, "res@example.com", f"AAAA-BBBB-CC{i}D")
        assert response.status_code == 400, i
    assert PasswordResetCode.objects.get().consumed_at is not None
    # the genuine code no longer works either
    other_ip = redeem_from(api_client, "10.1.1.1", "res@example.com", code)
    assert other_ip.status_code == 400


def redeem_from(client, ip, email, code):
    return client.post(REDEEM, {"email": email, "code": code, "new_password": NEW}, REMOTE_ADDR=ip)


def test_unknown_email_looks_the_same_as_a_wrong_code(api_client, setup):
    unknown = redeem(api_client, "nobody@example.com", "AAAA-BBBB-CCCC")
    wrong = redeem(api_client, "res@example.com", "AAAA-BBBB-CCCC")
    assert unknown.status_code == wrong.status_code == 400
    assert unknown.json() == wrong.json()


def test_weak_password_is_rejected_without_consuming_the_code(api_client, auth, setup):
    code = auth(setup["admin"]).post(issue_url(setup["resident"])).json()["code"]
    api_client.force_authenticate(None)
    weak = redeem(api_client, "res@example.com", code, "short")
    assert weak.status_code == 400 and "new_password" in weak.json()["error"]["details"]
    assert redeem(api_client, "res@example.com", code).status_code == 204


def test_reset_revokes_existing_sessions(api_client, auth, setup):
    tokens = login(api_client, "res@example.com", PASSWORD).json()
    code = auth(setup["admin"]).post(issue_url(setup["resident"])).json()["code"]
    api_client.force_authenticate(None)
    redeem(api_client, "res@example.com", code)
    refresh = api_client.post("/api/v1/auth/token/refresh/", {"refresh": tokens["refresh"]})
    assert refresh.status_code == 401


def test_reset_is_audited_without_secrets(api_client, auth, setup):
    code = auth(setup["admin"]).post(issue_url(setup["resident"])).json()["code"]
    api_client.force_authenticate(None)
    redeem(api_client, "res@example.com", code)
    issued = AuditLog.objects.get(action=actions.PASSWORD_RESET_ISSUED)
    assert issued.actor == setup["admin"] and issued.resource_id == str(setup["resident"].pk)
    assert issued.estate_id == setup["estate"].pk
    assert AuditLog.objects.filter(action=actions.PASSWORD_RESET_USED).exists()
    assert NEW not in str(list(AuditLog.objects.values()))


def test_estate_admin_cannot_reset_outside_their_estate_or_platform_admins_or_self(
    auth, setup, make_estate, make_member, platform_admin
):
    outsider = make_member(make_estate(), EstateRole.RESIDENT)
    client = auth(setup["admin"])
    assert client.post(issue_url(outsider)).status_code == 404
    assert client.post(issue_url(platform_admin)).status_code == 404
    assert client.post(issue_url(setup["admin"])).status_code == 404


def test_platform_admin_can_issue_codes_but_not_for_themselves(auth, setup, platform_admin):
    client = auth(platform_admin)
    assert client.post(issue_url(setup["resident"])).status_code == 201
    assert client.post(issue_url(platform_admin)).status_code == 404


@pytest.mark.parametrize(
    "role",
    [
        EstateRole.RESIDENT,
        EstateRole.ESTATE_MANAGER,
        EstateRole.SECURITY_SUPERVISOR,
        EstateRole.SECURITY_OFFICER,
    ],
)
def test_other_roles_cannot_issue_codes(auth, setup, make_member, role):
    actor = make_member(setup["estate"], role)
    assert auth(actor).post(issue_url(setup["resident"])).status_code == 403


def test_issuing_requires_authentication(api_client, setup):
    assert api_client.post(issue_url(setup["resident"])).status_code == 401


def test_redeem_endpoint_is_rate_limited(api_client, setup, monkeypatch):
    from rest_framework.throttling import ScopedRateThrottle

    monkeypatch.setitem(ScopedRateThrottle.THROTTLE_RATES, "password_reset", "2/min")
    codes = [redeem(api_client, "res@example.com", "AAAA-BBBB-CCCC").status_code for _ in range(3)]
    assert codes == [400, 400, 429]
