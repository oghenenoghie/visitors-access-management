"""Role permissions. Enforced on the backend for every protected endpoint.

Platform administrators act everywhere. Everyone else acts only through an active
membership of an active estate (see ``apps.common.scoping``).
"""

from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission

from apps.estates.models import Estate, EstateMembership, EstateRole


def active_memberships(user):
    return EstateMembership.objects.active().filter(user=user)


def administered_estate_ids(user):
    """Estates in which ``user`` is an active estate administrator."""
    return active_memberships(user).filter(role=EstateRole.ESTATE_ADMIN).values("estate_id")


def has_estate_role(user, roles, estate_id=None):
    if not user or not user.is_authenticated or not user.is_active:
        return False
    if user.is_platform_admin:
        return True
    qs = active_memberships(user).filter(role__in=roles)
    if estate_id is not None:
        qs = qs.filter(estate_id=estate_id)
    return qs.exists()


class IsPlatformAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_platform_admin)


class IsAdministrator(BasePermission):
    """Platform administrator or estate administrator."""

    def has_permission(self, request, view):
        return has_estate_role(request.user, [EstateRole.ESTATE_ADMIN])


class HasEstateRole(BasePermission):
    """Views declare ``allowed_roles``; object access still goes through scoped querysets."""

    def has_permission(self, request, view):
        roles = getattr(view, "allowed_roles", None)
        if not roles:
            return False
        return has_estate_role(request.user, roles)


def administrable_users(actor):
    """Users ``actor`` may administer (password reset, 2FA reset).

    Platform admins: everyone except themselves. Estate admins: members of estates they
    administer, never platform admins, never themselves.
    """
    users = get_user_model().objects.exclude(pk=actor.pk)
    if actor.is_platform_admin:
        return users
    return (
        users.filter(memberships__estate_id__in=administered_estate_ids(actor))
        .exclude(role="super_admin")
        .distinct()
    )


def shared_administered_estate(actor, target):
    """An estate the actor administers and the target belongs to, for audit scoping."""
    return (
        Estate.objects.filter(
            id__in=administered_estate_ids(actor),
            memberships__user=target,
        )
        .order_by("name")
        .first()
    )
