import pytest
from django.db import IntegrityError, transaction

from apps.users.models import PlatformRole, User


def test_create_user_normalises_email_and_hashes_password_with_argon2(db):
    user = User.objects.create_user(
        "Jane.Doe@Example.COM", "a-Long-test-passw0rd!", first_name="Jane", last_name="Doe"
    )
    assert user.email == "jane.doe@example.com"
    assert user.password.startswith("argon2$")
    assert user.check_password("a-Long-test-passw0rd!")
    assert user.role == PlatformRole.NONE
    assert not user.is_verified and not user.is_staff and not user.is_platform_admin


def test_user_id_is_a_uuid(db):
    user = User.objects.create_user("a@example.com", "a-Long-test-passw0rd!")
    assert len(str(user.id)) == 36


def test_email_is_required(db):
    with pytest.raises(ValueError):
        User.objects.create_user("", "a-Long-test-passw0rd!")


def test_email_uniqueness_is_case_insensitive_in_the_database(db):
    User.objects.create_user("b@example.com", "a-Long-test-passw0rd!")
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create(email="B@EXAMPLE.COM", first_name="x", last_name="y")


def test_superuser_is_platform_admin(db):
    admin = User.objects.create_superuser(
        "root@example.com", "a-Long-test-passw0rd!", first_name="Root", last_name="Admin"
    )
    assert admin.is_staff and admin.is_superuser and admin.is_verified
    assert admin.role == PlatformRole.SUPER_ADMIN
    assert admin.is_platform_admin


def test_inactive_super_admin_is_not_platform_admin(db):
    admin = User.objects.create_superuser("root@example.com", "a-Long-test-passw0rd!")
    admin.is_active = False
    assert not admin.is_platform_admin


def test_superuser_requires_staff_flag(db):
    with pytest.raises(ValueError):
        User.objects.create_superuser("r@example.com", "x", is_staff=False)


def test_admin_add_user_page_loads(client, db):
    admin = User.objects.create_superuser("root@example.com", "a-Long-test-passw0rd!")
    client.force_login(admin)
    assert client.get("/admin/users/user/add/").status_code == 200
    assert client.get("/admin/users/user/").status_code == 200
