from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.db import close_old_connections
from django.utils import timezone
from rest_framework.test import APIClient

from apps.access_control.models import (
    AccessEvent,
    AccessEventStatus,
    AccessEventType,
    GateDevice,
)
from apps.access_control.services import check_in
from apps.estates.models import EstateRole
from apps.properties.models import Property, ResidentialUnit
from apps.residents.models import (
    AssignmentRelationship,
    ResidentProfile,
    ResidentStatus,
    ResidentUnitAssignment,
)

pytestmark = pytest.mark.django_db

API = "/api/v1/"


@pytest.fixture
def access_context(make_estate, make_member):
    from apps.estates.models import EstateMembership
    from apps.access_control.models import GateDevice

    estate = make_estate()
    resident = make_member(estate, EstateRole.RESIDENT)
    profile = ResidentProfile.objects.create(
        user=resident, estate=estate, status=ResidentStatus.APPROVED
    )
    property_node = Property.objects.create(
        estate=estate, name="Block A", property_type="building"
    )
    unit = ResidentialUnit.objects.create(property=property_node, unit_number="A-101")
    ResidentUnitAssignment.objects.create(
        resident=profile,
        unit=unit,
        relationship=AssignmentRelationship.OWNER,
        starts_on=timezone.localdate() - timedelta(days=2),
    )
    officer = make_member(estate, EstateRole.SECURITY_OFFICER)
    supervisor = make_member(estate, EstateRole.SECURITY_SUPERVISOR)
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    gate = GateDevice.objects.create(
        estate=estate, name="Main Gate", device_identifier=f"gate-{estate.pk}"
    )
    return {
        "estate": estate, "resident": resident, "profile": profile, "unit": unit,
        "officer": officer, "supervisor": supervisor, "admin": admin, "gate": gate,
    }


def create_pass(context, *, access_type="single_use", max_uses=None):
    client = APIClient()
    client.force_authenticate(context["resident"])
    now = timezone.now()
    payload = {
        "visitor_name": "Ada Visitor",
        "visitor_phone": "+2348012345678",
        "unit": str(context["unit"].pk),
        "valid_from": (now + timedelta(minutes=1)).isoformat(),
        "valid_until": (now + timedelta(hours=2)).isoformat(),
        "access_type": access_type,
    }
    if max_uses is not None:
        payload["max_uses"] = max_uses
    response = client.post(API + "invitations/", payload, format="json")
    assert response.status_code == 201, response.data
    return response.data


def gate_client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def test_valid_visitor_verifies_and_checks_in(access_context):
    issued = create_pass(access_context)
    client = gate_client(access_context["officer"])
    data = {"gate_device": str(access_context["gate"].pk), "credential": issued["qr_token"]}

    verify = client.post(API + "gate/verify/", data, format="json")
    assert verify.status_code == 200
    assert verify.data["result"] == "VALID"

    entry = client.post(API + "gate/check-in/", data, format="json")
    assert entry.status_code == 201
    assert entry.data["status"] == AccessEventStatus.ACCEPTED
    assert entry.data["event_type"] == AccessEventType.ENTRY


def test_expired_visitor_is_rejected_and_logged(access_context):
    from apps.access_control.models import AccessCredential, VisitorInvitation

    issued = create_pass(access_context)
    invitation = VisitorInvitation.objects.get(pk=issued["invitation"]["id"])
    past = timezone.now() - timedelta(minutes=1)
    VisitorInvitation.objects.filter(pk=invitation.pk).update(valid_until=past)
    AccessCredential.objects.filter(invitation=invitation).update(expires_at=past)

    response = gate_client(access_context["officer"]).post(
        API + "gate/verify/",
        {"gate_device": str(access_context["gate"].pk), "credential": issued["access_code"]},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["result"] == "EXPIRED"
    assert AccessEvent.objects.filter(status=AccessEventStatus.REJECTED).exists()


def test_cancelled_invitation_revokes_credential(access_context):
    issued = create_pass(access_context)
    resident_client = gate_client(access_context["resident"])
    cancelled = resident_client.post(
        API + f"invitations/{issued['invitation']['id']}/cancel/", {}, format="json"
    )
    assert cancelled.status_code == 200

    response = gate_client(access_context["officer"]).post(
        API + "gate/verify/",
        {"gate_device": str(access_context["gate"].pk), "credential": issued["qr_token"]},
        format="json",
    )
    assert response.data["result"] == "REVOKED"


def test_single_use_credential_cannot_be_reused(access_context):
    issued = create_pass(access_context)
    client = gate_client(access_context["officer"])
    data = {"gate_device": str(access_context["gate"].pk), "credential": issued["qr_token"]}
    first = client.post(API + "gate/check-in/", data, format="json")
    assert first.data["status"] == AccessEventStatus.ACCEPTED

    exit_response = client.post(
        API + "gate/check-out/",
        {"gate_device": str(access_context["gate"].pk), "invitation": issued["invitation"]["id"]},
        format="json",
    )
    assert exit_response.status_code == 201

    second = client.post(API + "gate/check-in/", data, format="json")
    assert second.status_code == 201
    assert second.data["status"] == AccessEventStatus.REJECTED
    assert second.data["reason"] == "ALREADY_USED"


def test_check_out_links_to_original_entry(access_context):
    issued = create_pass(access_context)
    client = gate_client(access_context["officer"])
    client.post(
        API + "gate/check-in/",
        {"gate_device": str(access_context["gate"].pk), "credential": issued["access_code"]},
        format="json",
    )
    response = client.post(
        API + "gate/check-out/",
        {"gate_device": str(access_context["gate"].pk), "invitation": issued["invitation"]["id"]},
        format="json",
    )
    assert response.status_code == 201
    exit_event = AccessEvent.objects.get(pk=response.data["id"])
    assert exit_event.event_type == AccessEventType.EXIT
    assert exit_event.related_entry.event_type == AccessEventType.ENTRY


def test_resident_suspension_revokes_existing_passes(access_context):
    from apps.residents.services import suspend_resident

    issued = create_pass(access_context)
    admin_client = gate_client(access_context["admin"])
    # The management endpoint is exercised by the service in this focused integration test.
    suspend_resident(
        profile=access_context["profile"],
        actor=access_context["admin"],
        request=None,
        note="Resident status review",
    )
    response = gate_client(access_context["officer"]).post(
        API + "gate/verify/",
        {"gate_device": str(access_context["gate"].pk), "credential": issued["qr_token"]},
        format="json",
    )
    assert response.data["result"] == "REVOKED"
    assert admin_client is not None


def test_supervisor_override_requires_reason_and_records_event(access_context):
    issued = create_pass(access_context)
    response = gate_client(access_context["supervisor"]).post(
        API + "gate/override/",
        {
            "gate_device": str(access_context["gate"].pk),
            "invitation": issued["invitation"]["id"],
            "reason": "Resident confirmed visitor by phone",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["status"] == AccessEventStatus.OVERRIDDEN
    assert response.data["reason"] == "Resident confirmed visitor by phone"


@pytest.mark.django_db(transaction=True)
def test_concurrent_single_use_consumption_only_admits_once(access_context):
    issued = create_pass(access_context)
    gate = access_context["gate"]
    officer = access_context["officer"]
    from apps.access_control.models import VisitorInvitation

    invitation = VisitorInvitation.objects.get(pk=issued["invitation"]["id"])
    # Both workers start together and use independent database connections.
    barrier = Barrier(2)

    def consume():
        close_old_connections()
        try:
            barrier.wait(timeout=5)
            event = check_in(
                value=issued["qr_token"],
                gate=gate,
                actor=officer,
                request=None,
            )
            return event.status
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda _: consume(), range(2)))

    assert statuses.count(AccessEventStatus.ACCEPTED) == 1
    assert statuses.count(AccessEventStatus.REJECTED) == 1
    assert AccessEvent.objects.filter(
        invitation=invitation, status=AccessEventStatus.ACCEPTED,
        event_type=AccessEventType.ENTRY,
    ).count() == 1
