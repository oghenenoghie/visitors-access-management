from django.db import transaction
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.audit_logs.services import record
from apps.common.permissions import has_estate_role
from apps.estates.models import EstateRole

from .models import Property, ResidentialUnit
from .permissions import CanManageProperties
from .serializers import PropertySerializer, ResidentialUnitSerializer


class EstateScopedWriteViewSet(
    mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet
):
    """Read within active estates; write only for platform or estate administrators."""

    permission_classes = [IsAuthenticated]
    write_permission = CanManageProperties

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update"):
            return [self.write_permission()]
        return [permission() for permission in self.permission_classes]

    def _check_estate_write(self, estate_id):
        user = self.request.user
        if user.is_platform_admin:
            return
        if not has_estate_role(user, [EstateRole.ESTATE_ADMIN], estate_id=estate_id):
            from rest_framework.exceptions import NotFound

            raise NotFound()

    def perform_create(self, serializer):
        estate = serializer.validated_data.get("estate")
        if estate is None and "property" in serializer.validated_data:
            estate = serializer.validated_data["property"].estate
        self._check_estate_write(estate.pk)
        with transaction.atomic():
            instance = serializer.save()
            record(
                action=f"{instance._meta.model_name}.created",
                actor=self.request.user,
                estate=estate,
                resource=instance,
                new_values=serializer.data,
                request=self.request,
            )

    def perform_update(self, serializer):
        instance = serializer.instance
        estate = instance.estate if hasattr(instance, "estate_id") else instance.property.estate
        self._check_estate_write(estate.pk)
        with transaction.atomic():
            previous = self.get_serializer(instance).data
            updated = serializer.save()
            record(
                action=f"{updated._meta.model_name}.updated",
                actor=self.request.user,
                estate=estate,
                resource=updated,
                previous_values=previous,
                new_values=serializer.data,
                request=self.request,
            )


class PropertyViewSet(EstateScopedWriteViewSet):
    serializer_class = PropertySerializer
    queryset = Property.objects.none()
    search_fields = ["name", "estate__name", "estate__estate_code"]
    filterset_fields = ["estate", "property_type", "status", "parent"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        return Property.objects.for_user(self.request.user).select_related("estate", "parent")


class ResidentialUnitViewSet(EstateScopedWriteViewSet):
    serializer_class = ResidentialUnitSerializer
    queryset = ResidentialUnit.objects.none()
    search_fields = ["unit_number", "block", "property__name"]
    filterset_fields = ["property", "property__estate", "status", "block"]
    ordering_fields = ["unit_number", "created_at"]

    def get_queryset(self):
        return ResidentialUnit.objects.for_user(self.request.user).select_related(
            "property", "property__estate"
        )
