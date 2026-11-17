import pytest
from django.db import DatabaseError, connection, transaction

from apps.audit_logs import actions
from apps.audit_logs.models import AppendOnlyError, AuditLog
from apps.audit_logs.services import record
from apps.estates.models import EstateRole

URL = "/api/v1/admin/audit-logs/"


def test_record_stores_actor_estate_and_redacts_secrets(make_user, make_estate):
    user, estate = make_user(), make_estate()
    entry = record(
        action="test.action",
        actor=user,
        estate=estate,
        resource=estate,
        new_values={"name": "X", "password": "hunter2", "code": "ABCD", "estate_code": "E1"},
    )
    assert entry.actor_email == user.email
    assert entry.resource_type == "estates.estate" and entry.resource_id == str(estate.pk)
    assert entry.new_values == {
        "name": "X",
        "password": "[redacted]",
        "code": "[redacted]",
        "estate_code": "E1",
    }


def test_model_refuses_update_and_delete(db):
    entry = record(action="test.action")
    entry.action = "changed"
    with pytest.raises(AppendOnlyError):
        entry.save()
    with pytest.raises(AppendOnlyError):
        entry.delete()


def test_database_trigger_blocks_update_and_delete_even_with_raw_sql(db):
    entry = record(action="test.action")
    with pytest.raises(DatabaseError), transaction.atomic():
        AuditLog.objects.filter(pk=entry.pk).update(action="tampered")
    with pytest.raises(DatabaseError), transaction.atomic():
        AuditLog.objects.filter(pk=entry.pk).delete()
    with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("DELETE FROM audit_logs_auditlog")
    assert AuditLog.objects.filter(pk=entry.pk, action="test.action").exists()


def test_audit_api_requires_authentication(api_client, db):
    assert api_client.get(URL).status_code == 401


def test_audit_api_forbidden_for_non_administrators(auth, make_estate, make_member):
    estate = make_estate()
    for role in (EstateRole.RESIDENT, EstateRole.ESTATE_MANAGER, EstateRole.SECURITY_OFFICER):
        assert auth(make_member(estate, role)).get(URL).status_code == 403


def test_estate_admin_sees_only_their_estates_entries(auth, make_estate, make_member):
    mine, other = make_estate(), make_estate()
    record(action=actions.LOGIN_SUCCESS, estate=mine)
    record(action=actions.LOGIN_SUCCESS, estate=other)
    record(action=actions.LOGIN_FAILED)  # platform-level, no estate
    admin = make_member(mine, EstateRole.ESTATE_ADMIN)
    results = auth(admin).get(URL).json()["results"]
    assert [r["estate_id"] for r in results] == [str(mine.pk)]


def test_platform_admin_sees_everything_and_can_filter(auth, platform_admin, make_estate):
    estate = make_estate()
    record(action=actions.LOGIN_SUCCESS, estate=estate)
    record(action=actions.LOGIN_FAILED)
    client = auth(platform_admin)
    assert client.get(URL).json()["count"] == 2
    filtered = client.get(URL, {"action": actions.LOGIN_FAILED}).json()
    assert filtered["count"] == 1


def test_audit_api_is_read_only(auth, platform_admin):
    client = auth(platform_admin)
    assert client.post(URL, {}, format="json").status_code == 405
