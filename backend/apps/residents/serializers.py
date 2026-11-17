from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.estates.models import Estate, EstateStatus
from apps.users.models import User

from .models import ResidentProfile, ResidentStatus


class ResidentRegistrationSerializer(serializers.Serializer):
    estate_code = serializers.CharField(max_length=32)
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=128, min_length=10
    )
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=16, required=False, allow_blank=True)

    def validate_estate_code(self, value):
        estate = Estate.objects.filter(
            estate_code__iexact=value.strip(), status=EstateStatus.ACTIVE
        ).first()
        if estate is None:
            raise serializers.ValidationError("The estate reference is invalid.")
        self.context["estate"] = estate
        return estate.estate_code

    def validate_email(self, value):
        value = User.objects.normalize_email(value).lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate(self, attrs):
        candidate = User(
            email=attrs["email"],
            first_name=attrs["first_name"],
            last_name=attrs["last_name"],
        )
        validate_password(attrs["password"], user=candidate)
        return attrs


class ResidentProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)
    estate_id = serializers.UUIDField(read_only=True)
    estate_name = serializers.CharField(source="estate.name", read_only=True)
    estate_code = serializers.CharField(source="estate.estate_code", read_only=True)
    reviewed_by_email = serializers.EmailField(source="reviewed_by.email", read_only=True)

    class Meta:
        model = ResidentProfile
        fields = [
            "id", "user_id", "email", "first_name", "last_name", "phone_number",
            "estate_id", "estate_name", "estate_code", "status", "submitted_at",
            "reviewed_at", "reviewed_by_email", "review_note",
        ]
        read_only_fields = fields


class ResidentReviewSerializer(serializers.Serializer):
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)
