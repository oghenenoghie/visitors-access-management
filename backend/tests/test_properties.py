from django.db import IntegrityError, transaction

import pytest

from apps.audit_logs.models import AuditLog
from apps.estates.models import EstateRole


pytestmark = pytest.mark.django_db

PROPERTIES = "/api/v1/properties/"
UNITS = "/api/v1/residential-units/"


def test_estate_admin_can_create_property_and_unit(
    api_client, auth, make_estate, make_member
):
    estate = make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    auth(admin)

    street = api_client.post(
        PROPERTIES,
        {"estate_id": str(estate.pk), "name": "Palm Avenue", "property_type": "street"},
        format="json",
    )
    assert street.status_code == 201
    street_id = street.json()["id"]

    unit = api_client.post(
        UNITS,
        {"property_id": street_id, "unit_number": "A-101", "block": "A", "floor": "1"},
        format="json",
    )
    assert unit.status_code == 201
    assert unit.json()["estate_id"] == str(estate.pk)
    assert AuditLog.objects.filter(action="property.created", actor=admin).exists()
    assert AuditLog.objects.filter(action="residentialunit.created", actor=admin).exists()


def test_resident_can_read_but_cannot_write_property_records(
    api_client, auth, make_estate, make_member
):
    from apps.properties.models import Property

    estate = make_estate()
    resident = make_member(estate, EstateRole.RESIDENT)
    property_record = Property.objects.create(
        estate=estate, name="Oak Street", property_type="street"
    )
    auth(resident)

    response = api_client.get(PROPERTIES)
    assert response.status_code == 200
    assert str(property_record.pk) in str(response.json())

    denied = api_client.post(
        PROPERTIES,
        {"estate_id": str(estate.pk), "name": "Private Street", "property_type": "street"},
        format="json",
    )
    assert denied.status_code == 403


def test_other_estate_records_are_not_visible(
    api_client, auth, make_estate, make_member
):
    from apps.properties.models import Property

    own_estate, other_estate = make_estate(), make_estate()
    resident = make_member(own_estate, EstateRole.RESIDENT)
    foreign = Property.objects.create(
        estate=other_estate, name="Foreign Street", property_type="street"
    )
    auth(resident)

    response = api_client.get(PROPERTIES)
    assert response.status_code == 200
    assert str(foreign.pk) not in str(response.json())


def test_property_parent_must_belong_to_same_estate(
    api_client, auth, make_estate, make_member
):
    from apps.properties.models import Property

    estate, other_estate = make_estate(), make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    foreign_parent = Property.objects.create(
        estate=other_estate, name="Foreign Block", property_type="block"
    )
    auth(admin)

    response = api_client.post(
        PROPERTIES,
        {
            "estate_id": str(estate.pk),
            "parent_id": str(foreign_parent.pk),
            "name": "Building 1",
            "property_type": "building",
        },
        format="json",
    )
    assert response.status_code == 400
    assert "parent_id" in response.json()["error"]["details"]


def test_property_and_unit_deletion_are_not_exposed(
    api_client, auth, make_estate, make_member
):
    from apps.properties.models import Property

    estate = make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    item = Property.objects.create(estate=estate, name="Maple Street", property_type="street")
    auth(admin)

    response = api_client.delete(f"{PROPERTIES}{item.pk}/")
    assert response.status_code == 405
    assert Property.objects.filter(pk=item.pk).exists()


def test_duplicate_unit_location_is_rejected(
    make_estate, make_member
):
    from apps.properties.models import Property, ResidentialUnit

    estate = make_estate()
    Property.objects.create(estate=estate, name="Cedar Block", property_type="block")
    parent = Property.objects.get(estate=estate)
    ResidentialUnit.objects.create(property=parent, unit_number="12", block="A")
    with pytest.raises(IntegrityError), transaction.atomic():
        ResidentialUnit.objects.create(property=parent, unit_number="12", block="A")

def test_property_cannot_be_moved_to_another_estate(
    api_client, auth, make_estate, make_member
):
    from apps.properties.models import Property

    own, other = make_estate(), make_estate()
    admin = make_member(own, EstateRole.ESTATE_ADMIN)
    item = Property.objects.create(
        estate=own, name="Protected Street", property_type="street"
    )
    auth(admin)

    response = api_client.patch(
        f"{PROPERTIES}{item.pk}/",
        {"estate_id": str(other.pk)},
        format="json",
    )

    assert response.status_code == 400
    item.refresh_from_db()
    assert item.estate_id == own.pk
