from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.audit_logs.services import record
from apps.estates.models import EstateMembership, EstateRole, MembershipStatus
from apps.properties.models import PropertyStatus
from apps.residents.models import (
    AssignmentStatus,
    ResidentProfile,
    ResidentStatus,
    ResidentUnitAssignment,
)

from .credentials import issue_secret
from .models import (
    AccessCredential,
    AccessEvent,
    AccessEventStatus,
    AccessEventType,
    AccessType,
    CredentialStatus,
    GateDevice,
    GateDeviceStatus,
    InvitationStatus,
    Visitor,
    VisitorInvitation,
)

MAX_INVITATION_DAYS = 30


def _active_resident(*, actor, unit, now):
    profile = (
        ResidentProfile.objects.select_related("estate", "user")
        .filter(user=actor, estate_id=unit.property.estate_id, status=ResidentStatus.APPROVED)
        .first()
    )
    if profile is None:
        raise PermissionDenied("An approved resident profile is required.")
    membership = EstateMembership.objects.filter(
        user=actor,
        estate_id=profile.estate_id,
        role__in=[EstateRole.RESIDENT, EstateRole.HOUSEHOLD_MEMBER],
        status=MembershipStatus.ACTIVE,
        estate__status="active",
    ).exists()
    if not membership or not actor.is_active:
        raise PermissionDenied("Your resident membership is not active.")
    assignment = (
        ResidentUnitAssignment.objects.filter(
            resident=profile,
            unit=unit,
            status=AssignmentStatus.ACTIVE,
            starts_on__lte=now.date(),
        )
        .filter(Q(ends_on__isnull=True) | Q(ends_on__gte=now.date()))
        .exists()
    )
    if not assignment:
        raise PermissionDenied("You are not currently assigned to this residential unit.")
    return profile


@transaction.atomic
def create_invitation(*, actor, data, request):
    now = timezone.now()
    unit = data["unit"]
    if unit.status != PropertyStatus.ACTIVE or unit.property.status != PropertyStatus.ACTIVE:
        raise ValidationError({"unit": "The selected unit is not active."})
    profile = _active_resident(actor=actor, unit=unit, now=now)
    valid_from, valid_until = data["valid_from"], data["valid_until"]
    if valid_from < now - timedelta(minutes=1):
        raise ValidationError({"valid_from": "The invitation cannot start in the past."})
    if valid_until - valid_from > timedelta(days=MAX_INVITATION_DAYS):
        raise ValidationError({"valid_until": "An invitation cannot exceed 30 days."})
    access_type = data["access_type"]
    max_uses = 1 if access_type == AccessType.SINGLE_USE else data.get("max_uses", 10)
    visitor = Visitor.objects.create(
        full_name=data["visitor_name"].strip(),
        phone_number=data.get("visitor_phone", "").strip(),
        vehicle_registration=data.get("vehicle_registration", "").strip().upper(),
    )
    invitation = VisitorInvitation.objects.create(
        visitor=visitor,
        resident=profile,
        estate=profile.estate,
        unit=unit,
        created_by=actor,
        valid_from=valid_from,
        valid_until=valid_until,
        access_type=access_type,
        max_uses=max_uses,
    )
    credential = None
    for _attempt in range(5):
        qr_token, access_code, qr_hash, code_hash = issue_secret()
        try:
            # Isolate a unique-hash collision in a savepoint so a retry remains possible.
            with transaction.atomic():
                credential = AccessCredential.objects.create(
                    invitation=invitation,
                    qr_token_hash=qr_hash,
                    access_code_hash=code_hash,
                    expires_at=valid_until,
                )
            break
        except IntegrityError:
            continue
    if credential is None:
        raise ValidationError({"credential": "Unable to issue a unique credential. Retry."})
    record(
        action="invitation.created",
        actor=actor,
        estate=profile.estate,
        resource=invitation,
        new_values={
            "visitor_id": str(visitor.pk),
            "unit_id": str(unit.pk),
            "access_type": access_type,
            "valid_until": valid_until,
        },
        request=request,
    )
    return invitation, credential, qr_token, access_code


@transaction.atomic
def cancel_invitation(*, invitation, actor, request):
    credential = (
        AccessCredential.objects.select_for_update().filter(invitation_id=invitation.pk).first()
    )
    invitation = (
        VisitorInvitation.objects.select_for_update().select_related("estate").get(pk=invitation.pk)
    )
    if invitation.status != InvitationStatus.ACTIVE:
        raise ValidationError({"status": "Only active invitations can be cancelled."})
    invitation.status = InvitationStatus.CANCELLED
    invitation.save(update_fields=["status", "updated_at"])
    if credential:
        credential.status = CredentialStatus.REVOKED
        credential.save(update_fields=["status", "updated_at"])
    record(
        action="invitation.cancelled",
        actor=actor,
        estate=invitation.estate,
        resource=invitation,
        previous_values={"status": InvitationStatus.ACTIVE},
        new_values={"status": InvitationStatus.CANCELLED},
        request=request,
    )
    return invitation


def _gate_for_actor(*, actor, gate_id, allowed_roles):
    gate = (
        GateDevice.objects.filter(pk=gate_id, status=GateDeviceStatus.ACTIVE)
        .select_related("estate")
        .first()
    )
    if gate is None:
        raise PermissionDenied("The gate device is unavailable.")
    if (
        not actor.is_platform_admin
        and not EstateMembership.objects.filter(
            user=actor,
            estate=gate.estate,
            role__in=allowed_roles,
            status=MembershipStatus.ACTIVE,
            estate__status="active",
        ).exists()
    ):
        raise PermissionDenied("You are not assigned to this gate's estate.")
    if not actor.is_active:
        raise PermissionDenied("Your account is inactive.")
    return gate


def _lookup_credential(value):
    from .credentials import digest_secret

    digest = digest_secret(value.strip())
    return (
        AccessCredential.objects.select_related(
            "invitation__visitor", "invitation__estate", "invitation__unit"
        )
        .filter(Q(qr_token_hash=digest) | Q(access_code_hash=digest))
        .first()
    )


def _validation_result(credential, now):
    invitation = credential.invitation
    if (
        credential.status == CredentialStatus.REVOKED
        or invitation.status == InvitationStatus.CANCELLED
    ):
        return "REVOKED"
    if (
        credential.status == CredentialStatus.CONSUMED
        and invitation.access_type == AccessType.SINGLE_USE
    ):
        return "ALREADY_USED"
    if invitation.status != InvitationStatus.ACTIVE:
        return "CANCELLED"
    if now < invitation.valid_from:
        return "NOT_YET_VALID"
    if now >= invitation.valid_until or now >= credential.expires_at:
        return "EXPIRED"
    if credential.uses_count >= invitation.max_uses:
        return "ALREADY_USED"
    return "VALID"


def verify_credential(*, value, gate, actor, request):
    now = timezone.now()
    credential = _lookup_credential(value)
    if credential and credential.invitation.estate_id != gate.estate_id:
        credential = None
    result = _validation_result(credential, now) if credential else "INVALID"
    invitation = credential.invitation if credential else None
    if (
        result == "VALID"
        and AccessEvent.objects.filter(
            invitation=invitation,
            event_type=AccessEventType.ENTRY,
            status__in=[AccessEventStatus.ACCEPTED, AccessEventStatus.OVERRIDDEN],
        )
        .exclude(
            pk__in=AccessEvent.objects.filter(
                related_entry__isnull=False, event_type=AccessEventType.EXIT
            ).values("related_entry_id")
        )
        .exists()
    ):
        result = "ALREADY_CHECKED_IN"
    if result != "VALID":
        AccessEvent.objects.create(
            estate=gate.estate,
            invitation=invitation,
            credential=credential,
            gate_device=gate,
            officer=actor,
            event_type=AccessEventType.ENTRY,
            status=AccessEventStatus.REJECTED,
            occurred_at=now,
            reason=result,
        )
        record(
            action="access.verification_rejected",
            actor=actor,
            estate=gate.estate,
            resource=invitation,
            new_values={"result": result, "gate_id": str(gate.pk)},
            request=request,
        )
    return {
        "result": result,
        "visitor_name": invitation.visitor.full_name if result == "VALID" else None,
        "unit": invitation.unit.unit_number if result == "VALID" else None,
        "valid_until": invitation.valid_until if result == "VALID" else None,
    }, credential if result == "VALID" else None


@transaction.atomic
def check_in(*, value, gate, actor, request):
    credential = _lookup_credential(value)
    if credential and credential.invitation.estate_id != gate.estate_id:
        credential = None
    if credential is None:
        event = AccessEvent.objects.create(
            estate=gate.estate,
            gate_device=gate,
            officer=actor,
            event_type=AccessEventType.ENTRY,
            status=AccessEventStatus.REJECTED,
            occurred_at=timezone.now(),
            reason="INVALID",
        )
        record(
            action="access.check_in_rejected",
            actor=actor,
            estate=gate.estate,
            new_values={"result": "INVALID", "gate_id": str(gate.pk)},
            request=request,
        )
        return event
    credential = (
        AccessCredential.objects.select_for_update(of=("self",))
        .select_related("invitation__visitor", "invitation__estate", "invitation__unit")
        .get(pk=credential.pk)
    )
    invitation = VisitorInvitation.objects.select_for_update().get(pk=credential.invitation_id)
    result = _validation_result(credential, timezone.now())
    if (
        result == "VALID"
        and AccessEvent.objects.filter(
            invitation=invitation,
            event_type=AccessEventType.ENTRY,
            status__in=[AccessEventStatus.ACCEPTED, AccessEventStatus.OVERRIDDEN],
        )
        .exclude(
            pk__in=AccessEvent.objects.filter(
                related_entry__isnull=False, event_type=AccessEventType.EXIT
            ).values("related_entry_id")
        )
        .exists()
    ):
        result = "ALREADY_CHECKED_IN"
    if result != "VALID":
        event = AccessEvent.objects.create(
            estate=gate.estate,
            invitation=invitation,
            credential=credential,
            gate_device=gate,
            officer=actor,
            event_type=AccessEventType.ENTRY,
            status=AccessEventStatus.REJECTED,
            occurred_at=timezone.now(),
            reason=result,
        )
        record(
            action="access.check_in_rejected",
            actor=actor,
            estate=gate.estate,
            resource=invitation,
            new_values={"result": result, "gate_id": str(gate.pk)},
            request=request,
        )
        return event
    credential.uses_count += 1
    if (
        invitation.access_type == AccessType.SINGLE_USE
        or credential.uses_count >= invitation.max_uses
    ):
        credential.status = CredentialStatus.CONSUMED
    credential.save(update_fields=["uses_count", "status", "updated_at"])
    event = AccessEvent.objects.create(
        estate=gate.estate,
        invitation=invitation,
        credential=credential,
        gate_device=gate,
        officer=actor,
        event_type=AccessEventType.ENTRY,
        status=AccessEventStatus.ACCEPTED,
        occurred_at=timezone.now(),
    )
    record(
        action="access.checked_in",
        actor=actor,
        estate=gate.estate,
        resource=invitation,
        new_values={"event_id": str(event.pk), "gate_id": str(gate.pk)},
        request=request,
    )
    return event


@transaction.atomic
def check_out(*, invitation, gate, actor, request):
    invitation = (
        VisitorInvitation.objects.select_for_update()
        .select_related("visitor", "estate")
        .get(pk=invitation.pk)
    )
    exited_ids = AccessEvent.objects.filter(
        related_entry__isnull=False, event_type=AccessEventType.EXIT
    ).values("related_entry_id")
    entry = (
        AccessEvent.objects.select_for_update()
        .filter(
            invitation=invitation,
            event_type=AccessEventType.ENTRY,
            status__in=[AccessEventStatus.ACCEPTED, AccessEventStatus.OVERRIDDEN],
        )
        .exclude(pk__in=exited_ids)
        .order_by("-occurred_at")
        .first()
    )
    if entry is None:
        raise ValidationError({"invitation": "There is no active check-in for this visitor."})
    event = AccessEvent.objects.create(
        estate=gate.estate,
        invitation=invitation,
        credential=entry.credential,
        gate_device=gate,
        officer=actor,
        event_type=AccessEventType.EXIT,
        status=AccessEventStatus.ACCEPTED,
        occurred_at=timezone.now(),
        related_entry=entry,
    )
    record(
        action="access.checked_out",
        actor=actor,
        estate=gate.estate,
        resource=invitation,
        new_values={"event_id": str(event.pk), "entry_id": str(entry.pk)},
        request=request,
    )
    if invitation.access_type == AccessType.SINGLE_USE:
        invitation.status = InvitationStatus.COMPLETED
        invitation.save(update_fields=["status", "updated_at"])
    return event


@transaction.atomic
def manual_override(*, invitation, gate, actor, reason, request):
    if not reason or not reason.strip():
        raise ValidationError({"reason": "A justification is required."})
    credential = (
        AccessCredential.objects.select_for_update().filter(invitation_id=invitation.pk).first()
    )
    invitation = (
        VisitorInvitation.objects.select_for_update()
        .select_related("visitor")
        .get(pk=invitation.pk)
    )
    exited_ids = AccessEvent.objects.filter(
        related_entry__isnull=False, event_type=AccessEventType.EXIT
    ).values("related_entry_id")
    if (
        AccessEvent.objects.filter(
            invitation=invitation,
            event_type=AccessEventType.ENTRY,
            status__in=[AccessEventStatus.ACCEPTED, AccessEventStatus.OVERRIDDEN],
        )
        .exclude(pk__in=exited_ids)
        .exists()
    ):
        raise ValidationError({"invitation": "This visitor is already checked in."})
    if credential:
        credential.uses_count = min(invitation.max_uses, credential.uses_count + 1)
        credential.status = CredentialStatus.CONSUMED
        credential.save(update_fields=["uses_count", "status", "updated_at"])
    event = AccessEvent.objects.create(
        estate=gate.estate,
        invitation=invitation,
        credential=credential,
        gate_device=gate,
        officer=actor,
        event_type=AccessEventType.ENTRY,
        status=AccessEventStatus.OVERRIDDEN,
        occurred_at=timezone.now(),
        reason=reason.strip()[:500],
    )
    record(
        action="access.manual_override",
        actor=actor,
        estate=gate.estate,
        resource=invitation,
        new_values={"reason": reason.strip()[:500], "event_id": str(event.pk)},
        request=request,
    )
    return event
