from rest_framework import serializers

from apps.estates.models import EstateMembership
from apps.users.models import User

from .totp import is_enrolled


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
