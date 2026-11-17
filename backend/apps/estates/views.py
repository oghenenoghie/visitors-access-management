from django.db import transaction
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.audit_logs import actions
from apps.audit_logs.services import record
from apps.common.permissions import IsPlatformAdmin

from .models import Estate
from .serializers import EstateSerializer


class EstateViewSet(
    mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet
):
    """Estates. Everyone reads the estates they belong to; only platform admins write.

    Estates are never deleted: set ``status`` to ``inactive`` instead.
    """

    serializer_class = EstateSerializer
    queryset = Estate.objects.none()  # replaced per request; keeps schema generation working
    search_fields = ["name", "estate_code"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update"):
            return [IsPlatformAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Estate.objects.for_user(self.request.user).order_by("name")

    def perform_create(self, serializer):
        with transaction.atomic():
            estate = serializer.save()
            record(
                action=actions.ESTATE_CREATED,
                actor=self.request.user,
                estate=estate,
                resource=estate,
                new_values=serializer.data,
                request=self.request,
            )

    def perform_update(self, serializer):
        with transaction.atomic():
            previous = EstateSerializer(serializer.instance).data
            estate = serializer.save()
            record(
                action=actions.ESTATE_UPDATED,
                actor=self.request.user,
                estate=estate,
                resource=estate,
                previous_values=previous,
                new_values=serializer.data,
                request=self.request,
            )
