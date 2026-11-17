from rest_framework.permissions import BasePermission

from apps.common.permissions import has_estate_role
from apps.estates.models import EstateRole


class CanManageResidents(BasePermission):
    """Resident approvals and changes are estate-admin operations."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and has_estate_role(request.user, [EstateRole.ESTATE_ADMIN])
        )


class CanAccessResidentDocuments(BasePermission):
    """Only estate admins and the approved resident may access identity files."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, resident):
        user = request.user
        if user.is_platform_admin:
            return True
        if has_estate_role(user, [EstateRole.ESTATE_ADMIN], estate_id=resident.estate_id):
            return True
        return resident.user_id == user.pk and resident.status == "approved"
