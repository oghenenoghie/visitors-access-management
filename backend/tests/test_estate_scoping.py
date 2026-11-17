import pytest
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError, transaction

from apps.estates.models import Estate, EstateMembership, EstateRole, EstateStatus, MembershipStatus


def test_user_sees_only_estates_they_belong_to(make_user, make_estate, make_membership):
    e1, e2 = make_estate(), make_estate()
    user = make_user()
    make_membership(user, e1)
    assert list(Estate.objects.for_user(user)) == [e1]
    assert e2 not in Estate.objects.for_user(user)


def test_ended_and_suspended_memberships_grant_nothing(make_user, make_estate, make_membership):
    e1, e2 = make_estate(), make_estate()
    user = make_user()
    make_membership(user, e1, status=MembershipStatus.ENDED)
    make_membership(user, e2, status=MembershipStatus.SUSPENDED)
    assert not Estate.objects.for_user(user).exists()


def test_suspended_estate_grants_nothing(make_user, make_estate, make_membership):
    estate = make_estate(status=EstateStatus.SUSPENDED)
    user = make_user()
    make_membership(user, estate)
    assert not Estate.objects.for_user(user).exists()


def test_platform_admin_sees_every_estate(make_user, make_estate):
    make_estate(), make_estate()
    admin = make_user(role="super_admin")
    assert Estate.objects.for_user(admin).count() == 2


def test_inactive_platform_admin_sees_nothing(make_user, make_estate):
    make_estate()
    admin = make_user(role="super_admin", is_active=False)
    assert not Estate.objects.for_user(admin).exists()


def test_anonymous_and_none_see_nothing(make_estate):
    make_estate()
    assert not Estate.objects.for_user(AnonymousUser()).exists()
    assert not Estate.objects.for_user(None).exists()


def test_membership_queryset_is_scoped_by_estate(make_user, make_estate, make_membership):
    e1, e2 = make_estate(), make_estate()
    me, other = make_user(), make_user()
    mine = make_membership(me, e1, EstateRole.RESIDENT)
    make_membership(other, e2, EstateRole.RESIDENT)
    make_membership(other, e1, EstateRole.SECURITY_OFFICER)
    visible = set(EstateMembership.objects.for_user(me))
    assert mine in visible
    assert all(m.estate_id == e1.id for m in visible)


def test_user_has_one_membership_per_estate(make_user, make_estate, make_membership):
    estate, user = make_estate(), make_user()
    make_membership(user, estate)
    with pytest.raises(IntegrityError), transaction.atomic():
        make_membership(user, estate, EstateRole.ESTATE_ADMIN)


def test_estate_code_is_unique(make_estate):
    make_estate(estate_code="ABC1")
    with pytest.raises(IntegrityError), transaction.atomic():
        make_estate(estate_code="ABC1")


def test_estate_validation_rejects_bad_timezone_and_code(make_estate):
    from django.core.exceptions import ValidationError

    estate = Estate(name="X", estate_code="lower case", timezone="Mars/Olympus")
    with pytest.raises(ValidationError) as exc:
        estate.full_clean()
    assert "timezone" in exc.value.message_dict
    assert "estate_code" in exc.value.message_dict
