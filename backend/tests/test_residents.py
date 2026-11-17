import pytest

from apps.audit_logs.models import AuditLog
from apps.estates.models import EstateMembership, EstateRole, MembershipStatus
from apps.residents.models import ResidentProfile, ResidentStatus

pytestmark = pytest.mark.django_db

REGISTER = "/api/v1/residents/register/"
RESIDENTS = "/api/v1/residents/"


def registration_payload(estate, email="new.resident@example.com"):
    return {
        "estate_code": estate.estate_code,
        "email": email,
        "password": "A-strong-resident-passw0rd!",
        "first_name": "New",
        "last_name": "Resident",
        "phone_number": "+2348012345678",
    }


def test_registration_creates_pending_inactive_user_without_membership(api_client, make_estate):
    estate = make_estate()
    response = api_client.post(REGISTER, registration_payload(estate), format="json")

    assert response.status_code == 201
    profile = ResidentProfile.objects.get(user__email="new.resident@example.com")
    assert profile.status == ResidentStatus.PENDING
    assert profile.user.is_active is False
    assert not EstateMembership.objects.filter(user=profile.user, estate=estate).exists()
    assert response.json()["status"] == ResidentStatus.PENDING
    assert AuditLog.objects.filter(action="resident.registration_submitted").exists()


def test_invalid_or_inactive_estate_reference_is_rejected(api_client, make_estate):
    estate = make_estate(status="inactive")
    response = api_client.post(REGISTER, registration_payload(estate), format="json")
    assert response.status_code == 400
    assert not ResidentProfile.objects.exists()


def test_registration_rejects_weak_password(api_client, make_estate):
    estate = make_estate()
    payload = registration_payload(estate)
    payload["password"] = "password"
    response = api_client.post(REGISTER, payload, format="json")
    assert response.status_code == 400
    assert not ResidentProfile.objects.exists()


def test_estate_admin_can_approve_pending_resident(api_client, auth, make_estate, make_member):
    estate = make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    api_client.post(REGISTER, registration_payload(estate), format="json")
    profile = ResidentProfile.objects.get(user__email="new.resident@example.com")
    auth(admin)

    response = api_client.post(
        f"{RESIDENTS}{profile.pk}/approve/", {"note": "Verified"}, format="json"
    )

    assert response.status_code == 200
    profile.refresh_from_db()
    profile.user.refresh_from_db()
    membership = EstateMembership.objects.get(user=profile.user, estate=estate)
    assert profile.status == ResidentStatus.APPROVED
    assert profile.user.is_active is True
    assert membership.role == EstateRole.RESIDENT
    assert membership.status == MembershipStatus.ACTIVE
    assert profile.reviewed_by == admin
    assert AuditLog.objects.filter(action="resident.approved", actor=admin).exists()


def test_estate_admin_can_reject_registration_without_granting_access(
    api_client, auth, make_estate, make_member
):
    estate = make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    api_client.post(REGISTER, registration_payload(estate), format="json")
    profile = ResidentProfile.objects.get(user__email="new.resident@example.com")
    auth(admin)

    response = api_client.post(
        f"{RESIDENTS}{profile.pk}/reject/", {"note": "Unit details did not match"}, format="json"
    )

    assert response.status_code == 200
    profile.refresh_from_db()
    profile.user.refresh_from_db()
    assert profile.status == ResidentStatus.REJECTED
    assert profile.user.is_active is False
    assert not EstateMembership.objects.filter(user=profile.user, estate=estate).exists()


def test_resident_admin_list_is_scoped_to_administered_estates(
    api_client, auth, make_estate, make_member
):
    estate, other = make_estate(), make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    api_client.post(REGISTER, registration_payload(estate), format="json")
    api_client.post(
        REGISTER, registration_payload(other, "other.resident@example.com"), format="json"
    )
    auth(admin)

    response = api_client.get(RESIDENTS)
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["estate_id"] == str(estate.pk)


def test_resident_can_only_retrieve_own_profile(api_client, auth, make_estate, make_member):
    estate = make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    api_client.post(REGISTER, registration_payload(estate), format="json")
    profile = ResidentProfile.objects.get(user__email="new.resident@example.com")
    auth(admin)
    api_client.post(f"{RESIDENTS}{profile.pk}/approve/", {}, format="json")
    auth(profile.user)

    own = api_client.get(f"{RESIDENTS}{profile.pk}/")
    assert own.status_code == 200
    assert own.json()["id"] == str(profile.pk)


def test_non_admin_cannot_approve_resident(api_client, auth, make_estate, make_member):
    estate = make_estate()
    resident = make_member(estate, EstateRole.RESIDENT)
    api_client.post(REGISTER, registration_payload(estate), format="json")
    profile = ResidentProfile.objects.get(user__email="new.resident@example.com")
    auth(resident)

    response = api_client.post(f"{RESIDENTS}{profile.pk}/approve/", {}, format="json")
    assert response.status_code == 403


def test_suspension_revokes_estate_membership_without_affecting_other_estates(
    api_client, auth, make_estate, make_member, make_membership
):
    estate, other = make_estate(), make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    api_client.post(REGISTER, registration_payload(estate), format="json")
    profile = ResidentProfile.objects.get(user__email="new.resident@example.com")
    auth(admin)
    api_client.post(f"{RESIDENTS}{profile.pk}/approve/", {}, format="json")
    profile.refresh_from_db()
    make_membership(profile.user, other, EstateRole.RESIDENT)
    profile_other_membership = EstateMembership.objects.get(user=profile.user, estate=other)

    response = api_client.post(
        f"{RESIDENTS}{profile.pk}/suspend/", {"note": "Policy review"}, format="json"
    )

    assert response.status_code == 200
    profile.refresh_from_db()
    profile_other_membership.refresh_from_db()
    own_membership = EstateMembership.objects.get(user=profile.user, estate=estate)
    assert profile.status == ResidentStatus.SUSPENDED
    assert own_membership.status == MembershipStatus.SUSPENDED
    assert profile_other_membership.status == MembershipStatus.ACTIVE


def test_suspension_deactivates_account_when_no_other_active_estate_memberships(
    api_client, auth, make_estate, make_member
):
    estate = make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    api_client.post(REGISTER, registration_payload(estate), format="json")
    profile = ResidentProfile.objects.get(user__email="new.resident@example.com")
    auth(admin)
    api_client.post(f"{RESIDENTS}{profile.pk}/approve/", {}, format="json")

    response = api_client.post(
        f"{RESIDENTS}{profile.pk}/suspend/", {"note": "Access revoked"}, format="json"
    )

    assert response.status_code == 200
    profile.user.refresh_from_db()
    assert profile.user.is_active is False


def test_estate_manager_can_read_residents_but_cannot_approve(
    api_client, auth, make_estate, make_member
):
    estate = make_estate()
    manager = make_member(estate, EstateRole.ESTATE_MANAGER)
    api_client.post(REGISTER, registration_payload(estate), format="json")
    profile = ResidentProfile.objects.get(user__email="new.resident@example.com")
    auth(manager)

    listing = api_client.get(RESIDENTS)
    assert listing.status_code == 200
    assert listing.json()["results"][0]["id"] == str(profile.pk)

    denied = api_client.post(f"{RESIDENTS}{profile.pk}/approve/", {}, format="json")
    assert denied.status_code == 403
