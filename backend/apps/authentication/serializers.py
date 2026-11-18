from django.db import connection, transaction
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.backends import TokenBackendError
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.state import token_backend
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from apps.estates.models import EstateMembership
from apps.users.models import User

from .totp import is_enrolled


class RefreshCoordinationUnavailable(APIException):
    status_code = 503
    default_detail = "Refresh token rotation is temporarily unavailable."
    default_code = "refresh_coordination_unavailable"


class LockedTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Serialize refresh-token rotation across API workers using PostgreSQL row locks.

    Decode the signed token to identify its outstanding-token row, lock that row,
    then let Simple JWT perform blacklist validation and rotation while the lock
    is held. A concurrent request waits and observes the blacklist written by
    the first successful rotation.
    """

    def validate(self, attrs):
        if not connection.features.has_select_for_update:
            raise RefreshCoordinationUnavailable()

        raw_refresh = attrs["refresh"]
        try:
            payload = token_backend.decode(raw_refresh, verify=True)
            token_id = payload["jti"]
        except (TokenBackendError, KeyError) as exc:
            raise InvalidToken("Token is invalid or expired.") from exc

        with transaction.atomic():
            try:
                OutstandingToken.objects.select_for_update().get(jti=token_id)
            except OutstandingToken.DoesNotExist as exc:
                raise InvalidToken("Token is not recognized.") from exc
            return super().validate(attrs)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class ChallengeSerializer(serializers.Serializer):
    challenge_token = serializers.CharField()


class ChallengeCodeSerializer(ChallengeSerializer):
    code = serializers.CharField(max_length=32)


class AuthResponseSerializer(serializers.Serializer):
    """``status`` tells the client what to do next."""

    status = serializers.ChoiceField(
        choices=["authenticated", "two_factor_required", "two_factor_setup_required"]
    )
    access = serializers.CharField(required=False)
    refresh = serializers.CharField(required=False)
    challenge_token = serializers.CharField(required=False)
    recovery_codes = serializers.ListField(child=serializers.CharField(), required=False)


class EnrolmentResponseSerializer(serializers.Serializer):
    secret = serializers.CharField()
    otpauth_uri = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class PasswordResetRedeemSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=32)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)


class ResetCodeIssuedSerializer(serializers.Serializer):
    code = serializers.CharField()
    expires_at = serializers.DateTimeField()


class MembershipSerializer(serializers.ModelSerializer):
    estate_id = serializers.UUIDField(read_only=True)
    estate_code = serializers.CharField(source="estate.estate_code", read_only=True)

    class Meta:
        model = EstateMembership
        fields = ["estate_id", "estate_code", "role", "status"]


class MeSerializer(serializers.ModelSerializer):
    platform_role = serializers.CharField(source="role", read_only=True)
    two_factor_enabled = serializers.SerializerMethodField()
    memberships = MembershipSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "platform_role",
            "two_factor_enabled",
            "memberships",
        ]
        read_only_fields = fields

    def get_two_factor_enabled(self, user) -> bool:
        return is_enrolled(user)
