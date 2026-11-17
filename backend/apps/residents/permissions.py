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
