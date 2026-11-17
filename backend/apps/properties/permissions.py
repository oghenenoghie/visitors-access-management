from rest_framework.permissions import BasePermission

from apps.common.permissions import has_estate_role
from apps.estates.models import EstateRole


class CanManageProperties(BasePermission):
    """Property writes are limited to platform and estate administrators in M3."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_platform_admin or has_estate_role(user, [EstateRole.ESTATE_ADMIN]))
        )
