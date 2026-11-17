from rest_framework.permissions import BasePermission
from rest_framework.throttling import UserRateThrottle

from apps.estates.models import EstateMembership, EstateRole, MembershipStatus


class GateRolePermission(BasePermission):
    allowed_roles = [EstateRole.SECURITY_OFFICER, EstateRole.SECURITY_SUPERVISOR, EstateRole.ESTATE_ADMIN]

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active)


class CanOverrideAccess(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False
        if user.is_platform_admin:
            return True
        return EstateMembership.objects.filter(
            user=user,
            role__in=[EstateRole.SECURITY_SUPERVISOR, EstateRole.ESTATE_ADMIN],
            status=MembershipStatus.ACTIVE,
            estate__status="active",
        ).exists()


class GateAttemptThrottle(UserRateThrottle):
    """Limit credential guessing per authenticated gate officer."""

    rate = "30/min"
