from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser

from apps.common.permissions import (
    HasEstateRole,
    IsAdministrator,
    IsPlatformAdmin,
    administrable_users,
    has_estate_role,
)
from apps.estates.models import EstateRole, EstateStatus, MembershipStatus


def _request(user):
    return SimpleNamespace(user=user)


def test_has_estate_role_requires_an_active_membership_with_the_role(
    make_estate, make_member, make_user, make_membership
):
    estate = make_estate()
    officer = make_member(estate, EstateRole.SECURITY_OFFICER)
    assert has_estate_role(officer, [EstateRole.SECURITY_OFFICER])
    assert not has_estate_role(officer, [EstateRole.ESTATE_ADMIN])
    assert has_estate_role(officer, [EstateRole.SECURITY_OFFICER], estate_id=estate.id)
    assert not has_estate_role(officer, [EstateRole.SECURITY_OFFICER], estate_id=make_estate().id)

    suspended = make_user()
    make_membership(suspended, estate, EstateRole.SECURITY_OFFICER, status=MembershipStatus.ENDED)
    assert not has_estate_role(suspended, [EstateRole.SECURITY_OFFICER])


def test_suspended_estate_removes_roles(make_estate, make_member):
    estate = make_estate(status=EstateStatus.SUSPENDED)
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    assert not has_estate_role(admin, [EstateRole.ESTATE_ADMIN])


def test_anonymous_and_inactive_users_have_no_roles(make_estate, make_member, platform_admin):
    assert not has_estate_role(AnonymousUser(), [EstateRole.ESTATE_ADMIN])
    platform_admin.is_active = False
    assert not has_estate_role(platform_admin, [EstateRole.ESTATE_ADMIN])


def test_permission_classes(make_estate, make_member, platform_admin):
    estate = make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    resident = make_member(estate, EstateRole.RESIDENT)
    assert IsPlatformAdmin().has_permission(_request(platform_admin), None)
    assert not IsPlatformAdmin().has_permission(_request(admin), None)
    assert IsAdministrator().has_permission(_request(admin), None)
    assert IsAdministrator().has_permission(_request(platform_admin), None)
    assert not IsAdministrator().has_permission(_request(resident), None)

    view = SimpleNamespace(allowed_roles={EstateRole.RESIDENT})
    assert HasEstateRole().has_permission(_request(resident), view)
    assert not HasEstateRole().has_permission(_request(admin), view)
    assert not HasEstateRole().has_permission(_request(resident), SimpleNamespace())


def test_administrable_users(make_estate, make_member, platform_admin, make_user):
    e1, e2 = make_estate(), make_estate()
    admin = make_member(e1, EstateRole.ESTATE_ADMIN)
    peer = make_member(e1, EstateRole.ESTATE_ADMIN)
    resident = make_member(e1, EstateRole.RESIDENT)
    outsider = make_member(e2, EstateRole.RESIDENT)
    other_admin = make_user(role="super_admin")

    visible = set(administrable_users(admin))
    assert visible == {peer, resident}  # not self, not other estates, not platform admins
    everyone = set(administrable_users(platform_admin))
    assert {admin, peer, resident, outsider, other_admin} <= everyone
    assert platform_admin not in everyone
