from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit_logs.services import record
from apps.estates.models import EstateMembership, EstateRole, MembershipStatus

from .document_storage import store_identity_document
from .models import ResidentDocumentType, ResidentProfile, ResidentStatus

User = get_user_model()


@transaction.atomic
def register_resident(*, data, request):
    estate = data.pop("estate")
    identity_document = data.pop("identity_document", None)
    document_type = data.pop("identity_document_type", ResidentDocumentType.OTHER)
    user = User.objects.create_user(
        email=data["email"],
        password=data["password"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone_number=data.get("phone_number", ""),
        is_active=False,
    )
    profile = ResidentProfile.objects.create(user=user, estate=estate)
    if identity_document:
        store_identity_document(
            resident=profile,
            uploaded_file=identity_document,
            document_type=document_type,
            uploaded_by=user,
            request=request,
        )
    record(
        action="resident.registration_submitted",
        actor=user,
        estate=estate,
        resource=profile,
        new_values={"status": ResidentStatus.PENDING},
        request=request,
    )
    return profile


def _review(*, profile, actor, request, target_status, note=""):
    profile = (
        ResidentProfile.objects.select_for_update()
        .select_related("user", "estate")
        .get(pk=profile.pk)
    )
    if profile.status != ResidentStatus.PENDING:
        raise ValidationError({"status": "Only pending resident registrations can be reviewed."})

    previous_status = profile.status
    now = timezone.now()
    if target_status == ResidentStatus.APPROVED:
        membership, created = EstateMembership.objects.get_or_create(
            user=profile.user,
            estate=profile.estate,
            defaults={"role": EstateRole.RESIDENT, "status": MembershipStatus.ACTIVE},
        )
        if not created and membership.role != EstateRole.RESIDENT:
            raise ValidationError(
                {"membership": "This account already has a different role in the estate."}
            )
        if not created:
            membership.status = MembershipStatus.ACTIVE
            membership.save(update_fields=["status", "updated_at"])
        if not profile.user.is_active:
            profile.user.is_active = True
            profile.user.save(update_fields=["is_active", "updated_at"])

    profile.status = target_status
    profile.reviewed_at = now
    profile.reviewed_by = actor
    profile.review_note = note
    profile.save(
        update_fields=["status", "reviewed_at", "reviewed_by", "review_note", "updated_at"]
    )
    record(
        action=f"resident.{target_status}",
        actor=actor,
        estate=profile.estate,
        resource=profile,
        previous_values={"status": previous_status},
        new_values={"status": target_status, "review_note": note},
        request=request,
    )
    return profile


@transaction.atomic
def approve_resident(*, profile, actor, request, note=""):
    return _review(
        profile=profile,
        actor=actor,
        request=request,
        target_status=ResidentStatus.APPROVED,
        note=note,
    )


@transaction.atomic
def reject_resident(*, profile, actor, request, note=""):
    if not note.strip():
        raise ValidationError({"note": "A reason is required when rejecting a registration."})
    return _review(
        profile=profile,
        actor=actor,
        request=request,
        target_status=ResidentStatus.REJECTED,
        note=note,
    )


@transaction.atomic
def suspend_resident(*, profile, actor, request, note=""):
    profile = (
        ResidentProfile.objects.select_for_update()
        .select_related("user", "estate")
        .get(pk=profile.pk)
    )
    if profile.status != ResidentStatus.APPROVED:
        raise ValidationError({"status": "Only approved residents can be suspended."})
    membership = (
        EstateMembership.objects.select_for_update()
        .filter(user=profile.user, estate=profile.estate, role=EstateRole.RESIDENT)
        .first()
    )
    if membership is None:
        raise ValidationError({"membership": "The resident membership could not be found."})
    membership.status = MembershipStatus.SUSPENDED
    membership.save(update_fields=["status", "updated_at"])
    profile.status = ResidentStatus.SUSPENDED
    if (
        not EstateMembership.objects.active()
        .filter(user=profile.user)
        .exclude(estate=profile.estate)
        .exists()
    ):
        profile.user.is_active = False
        profile.user.save(update_fields=["is_active", "updated_at"])
    profile.reviewed_at = timezone.now()
    profile.reviewed_by = actor
    profile.review_note = note
    profile.save(
        update_fields=["status", "reviewed_at", "reviewed_by", "review_note", "updated_at"]
    )
    # Policy: suspending a resident immediately cancels all active visitor passes.
    from apps.access_control.models import (
        AccessCredential,
        CredentialStatus,
        InvitationStatus,
    )

    credentials = AccessCredential.objects.select_for_update().select_related(
        "invitation", "invitation__estate"
    ).filter(
        invitation__resident=profile,
        invitation__status=InvitationStatus.ACTIVE,
    )
    for credential in credentials:
        invitation = credential.invitation
        credential.status = CredentialStatus.REVOKED
        credential.save(update_fields=["status", "updated_at"])
        invitation.status = InvitationStatus.CANCELLED
        invitation.save(update_fields=["status", "updated_at"])
        record(
            action="invitation.revoked_by_resident_suspension",
            actor=actor,
            estate=invitation.estate,
            resource=invitation,
            previous_values={"status": InvitationStatus.ACTIVE},
            new_values={"status": InvitationStatus.CANCELLED},
            request=request,
        )

    record(
        action="resident.suspended",
        actor=actor,
        estate=profile.estate,
        resource=profile,
        previous_values={"status": ResidentStatus.APPROVED},
        new_values={"status": ResidentStatus.SUSPENDED, "review_note": note},
        request=request,
    )
    return profile
