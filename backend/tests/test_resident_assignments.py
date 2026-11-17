import pytest

from apps.estates.models import EstateRole
from apps.properties.models import Property, ResidentialUnit
from apps.residents.models import AssignmentStatus, ResidentProfile

pytestmark = pytest.mark.django_db

REGISTER = "/api/v1/residents/register/"
RESIDENTS = "/api/v1/residents/"
ASSIGNMENTS = "/api/v1/resident-unit-assignments/"


def registration_payload(estate):
    return {
        "estate_code": estate.estate_code,
        "email": "assigned.resident@example.com",
        "password": "A-strong-resident-passw0rd!",
        "first_name": "Assigned",
        "last_name": "Resident",
    }


def make_unit(estate, name="Block A", unit_number="A-101"):
    property_record = Property.objects.create(
        estate=estate, name=name, property_type="block"
    )
    return ResidentialUnit.objects.create(property=property_record, unit_number=unit_number)


def approved_profile(api_client, estate, admin):
    api_client.post(REGISTER, registration_payload(estate), format="json")
    profile = ResidentProfile.objects.get(user__email="assigned.resident@example.com")
    api_client.force_authenticate(admin)
    response = api_client.post(f"{RESIDENTS}{profile.pk}/approve/", {}, format="json")
    assert response.status_code == 200
    return profile


def assignment_payload(profile, unit, **overrides):
    payload = {
        "resident_id": str(profile.pk),
        "unit_id": str(unit.pk),
        "relationship": "tenant",
        "is_primary": True,
        "starts_on": "2026-01-01",
    }
    payload.update(overrides)
    return payload


def test_admin_can_assign_approved_resident_to_unit(
    api_client, auth, make_estate, make_member
):
    estate = make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    profile = approved_profile(api_client, estate, admin)
    unit = make_unit(estate)
    auth(admin)

    response = api_client.post(
        ASSIGNMENTS, assignment_payload(profile, unit), format="json"
    )

    assert response.status_code == 201
    assert response.json()["unit_id"] == str(unit.pk)
    assert response.json()["status"] == AssignmentStatus.ACTIVE


def test_pending_resident_cannot_be_assigned(
    api_client, auth, make_estate, make_member
):
    estate = make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    api_client.post(REGISTER, registration_payload(estate), format="json")
    profile = ResidentProfile.objects.get(user__email="assigned.resident@example.com")
    unit = make_unit(estate)
    auth(admin)

    response = api_client.post(
        ASSIGNMENTS, assignment_payload(profile, unit), format="json"
    )

    assert response.status_code == 400


def test_cross_estate_unit_assignment_is_rejected(
    api_client, auth, make_estate, make_member
):
    estate, other = make_estate(), make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    profile = approved_profile(api_client, estate, admin)
    foreign_unit = make_unit(other)
    auth(admin)

    response = api_client.post(
        ASSIGNMENTS, assignment_payload(profile, foreign_unit), format="json"
    )

    assert response.status_code == 400


def test_overlapping_primary_assignment_is_rejected(
    api_client, auth, make_estate, make_member
):
    estate = make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    profile = approved_profile(api_client, estate, admin)
    first, second = make_unit(estate), make_unit(estate, "Block B", "B-102")
    auth(admin)

    created = api_client.post(
        ASSIGNMENTS, assignment_payload(profile, first), format="json"
    )
    assert created.status_code == 201

    overlap = api_client.post(
        ASSIGNMENTS,
        assignment_payload(profile, second, starts_on="2026-02-01"),
        format="json",
    )
    assert overlap.status_code == 400


def test_resident_can_only_list_own_assignments(
    api_client, auth, make_estate, make_member
):
    estate = make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    profile = approved_profile(api_client, estate, admin)
    unit = make_unit(estate)
    auth(admin)
    created = api_client.post(
        ASSIGNMENTS, assignment_payload(profile, unit), format="json"
    )
    assert created.status_code == 201
    auth(profile.user)

    response = api_client.get(ASSIGNMENTS)
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1


def test_admin_can_end_assignment_and_reassign_unit(
    api_client, auth, make_estate, make_member
):
    estate = make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    profile = approved_profile(api_client, estate, admin)
    unit = make_unit(estate)
    auth(admin)
    created = api_client.post(
        ASSIGNMENTS, assignment_payload(profile, unit), format="json"
    )
    assignment_id = created.json()["id"]

    ended = api_client.post(
        f"{ASSIGNMENTS}{assignment_id}/end/",
        {"ends_on": "2026-02-01"},
        format="json",
    )

    assert ended.status_code == 200
    assert ended.json()["status"] == AssignmentStatus.ENDED
    assert ended.json()["ends_on"] == "2026-02-01"
    next_assignment = api_client.post(
        ASSIGNMENTS,
        assignment_payload(profile, unit, starts_on="2026-02-02"),
        format="json",
    )
    assert next_assignment.status_code == 201



def test_estate_admin_cannot_assign_another_estates_resident(
    api_client, auth, make_estate, make_member
):
    own, other = make_estate(), make_estate()
    admin = make_member(own, EstateRole.ESTATE_ADMIN)
    profile = approved_profile(api_client, other, make_member(other, EstateRole.ESTATE_ADMIN))
    unit = make_unit(other)
    auth(admin)

    response = api_client.post(
        ASSIGNMENTS, assignment_payload(profile, unit), format="json"
    )

    assert response.status_code == 400



def test_non_overlapping_primary_assignment_periods_are_allowed(
    api_client, auth, make_estate, make_member
):
    estate = make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    profile = approved_profile(api_client, estate, admin)
    first, second = make_unit(estate), make_unit(estate, "Block B", "B-202")
    auth(admin)

    first_assignment = api_client.post(
        ASSIGNMENTS,
        assignment_payload(profile, first, starts_on="2026-01-01", ends_on="2026-06-30"),
        format="json",
    )
    second_assignment = api_client.post(
        ASSIGNMENTS,
        assignment_payload(profile, second, starts_on="2026-07-01"),
        format="json",
    )

    assert first_assignment.status_code == 201
    assert second_assignment.status_code == 201
