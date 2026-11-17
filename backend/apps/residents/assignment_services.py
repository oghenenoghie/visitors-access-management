from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit_logs.services import record
from apps.properties.models import ResidentialUnit, PropertyStatus

from .assignments import AssignmentStatus, ResidentUnitAssignment
from .models import ResidentProfile, ResidentStatus


@transaction.atomic
def create_assignment(
    *, resident, unit, relationship, is_primary, starts_on, ends_on, actor, request
):
    resident = ResidentProfile.objects.select_for_update().select_related("estate", "user").get(
        pk=resident.pk
    )
    unit = ResidentialUnit.objects.select_related("property", "property__estate").get(pk=unit.pk)
    if resident.status != ResidentStatus.APPROVED:
        raise ValidationError({"resident": "Only approved residents can be assigned to a unit."})
    if resident.estate_id != unit.property.estate_id:
        raise ValidationError({"unit": "The unit must belong to the resident's estate."})
    if unit.status != PropertyStatus.ACTIVE or unit.property.status != PropertyStatus.ACTIVE:
        raise ValidationError({"unit": "The unit and its property must both be active."})
    if ends_on and ends_on < starts_on:
        raise ValidationError({"ends_on": "End date cannot precede start date."})

    overlaps = ResidentUnitAssignment.objects.filter(
        resident=resident,
        status=AssignmentStatus.ACTIVE,
        starts_on__lte=ends_on or timezone.localdate(),
    ).filter(Q(ends_on__isnull=True) | Q(ends_on__gte=starts_on))
    if is_primary:
        overlaps = overlaps.filter(is_primary=True)
    if overlaps.exists():
        raise ValidationError(
            {"assignment": "The requested dates overlap an existing active assignment."}
        )

    assignment = ResidentUnitAssignment.objects.create(
        resident=resident,
        unit=unit,
        relationship=relationship,
        is_primary=is_primary,
        starts_on=starts_on,
        ends_on=ends_on,
    )
    record(
        action="resident.unit_assigned",
        actor=actor,
        estate=resident.estate,
        resource=assignment,
        new_values={
            "resident_id": str(resident.pk),
            "unit_id": str(unit.pk),
            "relationship": relationship,
            "is_primary": is_primary,
            "starts_on": starts_on,
            "ends_on": ends_on,
        },
        request=request,
    )
    return assignment


@transaction.atomic
def end_assignment(*, assignment, ends_on, actor, request):
    assignment = ResidentUnitAssignment.objects.select_for_update().select_related(
        "resident__estate", "resident__user"
    ).get(pk=assignment.pk)
    if assignment.status != AssignmentStatus.ACTIVE:
        raise ValidationError({"status": "Only active assignments can be ended."})
    if ends_on < assignment.starts_on:
        raise ValidationError({"ends_on": "End date cannot precede start date."})
    assignment.status = AssignmentStatus.ENDED
    assignment.ends_on = ends_on
    assignment.save(update_fields=["status", "ends_on", "updated_at"])
    record(
        action="resident.unit_assignment_ended",
        actor=actor,
        estate=assignment.resident.estate,
        resource=assignment,
        previous_values={"status": AssignmentStatus.ACTIVE, "ends_on": None},
        new_values={"status": AssignmentStatus.ENDED, "ends_on": ends_on},
        request=request,
    )
    return assignment
