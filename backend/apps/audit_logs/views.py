import django_filters
from rest_framework import viewsets

from apps.common.permissions import IsAdministrator, administered_estate_ids

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogFilter(django_filters.FilterSet):
    created_after = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = AuditLog
        fields = ["action", "actor", "estate", "resource_type", "resource_id"]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit entries. Platform admins see everything; estate admins see their estates only."""

    serializer_class = AuditLogSerializer
    permission_classes = [IsAdministrator]
    filterset_class = AuditLogFilter
    ordering = ["-created_at"]
    queryset = AuditLog.objects.none()

    def get_queryset(self):
        user = self.request.user
        qs = AuditLog.objects.all()
        if user.is_platform_admin:
            return qs
        return qs.filter(estate_id__in=administered_estate_ids(user))
