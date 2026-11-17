from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower

from apps.common.models import BaseModel


class PlatformRole(models.TextChoices):
    """Platform-level role. Estate roles live on EstateMembership."""

    NONE = "none", "None"
    SUPER_ADMIN = "super_admin", "Super administrator"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        user = self.model(email=self.normalize_email(email).lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("role", PlatformRole.SUPER_ADMIN)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("A superuser must have is_staff and is_superuser set to True.")
        return self._create_user(email, password, **extra_fields)


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=254, unique=True)
    phone_number = models.CharField(
        max_length=16,
        blank=True,
        validators=[RegexValidator(r"^\+?[0-9]{7,15}$", "Enter a valid phone number.")],
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=PlatformRole.choices, default=PlatformRole.NONE)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        ordering = ["email"]
        constraints = [
            models.UniqueConstraint(Lower("email"), name="users_user_email_ci_unique"),
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_platform_admin(self):
        return self.is_active and self.role == PlatformRole.SUPER_ADMIN
