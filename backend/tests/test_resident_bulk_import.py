import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.estates.models import EstateMembership
from apps.properties.models import Property, ResidentialUnit
from apps.residents.models import ResidentProfile, ResidentStatus

pytestmark = pytest.mark.django_db

IMPORTS = "/api/v1/imports/"


def csv_file(name, content):
    return SimpleUploadedFile(name, content.encode("utf-8"), content_type="text/csv")


def test_unit_import_dry_run_does_not_write_records(
    api_client, auth, make_estate, make_member
):
    estate = make_estate()
    admin = make_member(estate, "estate_admin")
    property_record = Property.objects.create(
        estate=estate, name="Block A", property_type="block"
    )
    auth(admin)

    response = api_client.post(
        f"{IMPORTS}units/",
        {
            "estate_id": str(estate.pk),
            "dry_run": "true",
            "file": csv_file(
                "units.csv",
                f"property_id,unit_number,block\n{property_record.pk},A-101,A",
            ),
        },
        format="multipart",
    )

    assert response.status_code == 200
    assert response.json()["valid_rows"] == 1
    assert response.json()["committed"] is False
    assert not ResidentialUnit.objects.exists()


def test_unit_import_commit_creates_units_atomically(
    api_client, auth, make_estate, make_member
):
    estate = make_estate()
    admin = make_member(estate, "estate_admin")
    property_record = Property.objects.create(
        estate=estate, name="Block A", property_type="block"
    )
    auth(admin)

    response = api_client.post(
        f"{IMPORTS}units/",
        {
            "estate_id": str(estate.pk),
            "dry_run": "false",
            "file": csv_file(
                "units.csv",
                f"property_id,unit_number,block\n{property_record.pk},A-101,A\n{property_record.pk},A-102,A",
            ),
        },
        format="multipart",
    )

    assert response.status_code == 201
    assert response.json()["committed"] is True
    assert ResidentialUnit.objects.filter(property=property_record).count() == 2


def test_unit_import_with_errors_does_not_partially_commit(
    api_client, auth, make_estate, make_member
):
    estate = make_estate()
    admin = make_member(estate, "estate_admin")
    property_record = Property.objects.create(
        estate=estate, name="Block A", property_type="block"
    )
    ResidentialUnit.objects.create(property=property_record, unit_number="A-101")
    auth(admin)

    response = api_client.post(
        f"{IMPORTS}units/",
        {
            "estate_id": str(estate.pk),
            "dry_run": "false",
            "file": csv_file(
                "units.csv",
                f"property_id,unit_number\n{property_record.pk},A-102\n{property_record.pk},A-101",
            ),
        },
        format="multipart",
    )

    assert response.status_code == 400
    assert ResidentialUnit.objects.filter(property=property_record).count() == 1


def test_resident_import_creates_pending_inactive_profiles(
    api_client, auth, make_estate, make_member
):
    estate = make_estate()
    admin = make_member(estate, "estate_admin")
    auth(admin)

    response = api_client.post(
        f"{IMPORTS}residents/",
        {
            "estate_id": str(estate.pk),
            "dry_run": "false",
            "file": csv_file(
                "residents.csv",
                "email,first_name,last_name\nimported@example.com,Imported,Resident",
            ),
        },
        format="multipart",
    )

    assert response.status_code == 201
    profile = ResidentProfile.objects.get(user__email="imported@example.com")
    profile.user.refresh_from_db()
    assert profile.status == ResidentStatus.PENDING
    assert profile.user.is_active is False
    assert not EstateMembership.objects.filter(user=profile.user, estate=estate).exists()


def test_admin_cannot_import_into_another_estate(
    api_client, auth, make_estate, make_member
):
    own, other = make_estate(), make_estate()
    admin = make_member(own, "estate_admin")
    auth(admin)

    response = api_client.post(
        f"{IMPORTS}residents/",
        {
            "estate_id": str(other.pk),
            "dry_run": "true",
            "file": csv_file(
                "residents.csv",
                "email,first_name,last_name\nimported@example.com,Imported,Resident",
            ),
        },
        format="multipart",
    )

    assert response.status_code == 404
    assert not ResidentProfile.objects.exists()
