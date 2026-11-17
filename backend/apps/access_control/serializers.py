from rest_framework import serializers

from apps.properties.models import ResidentialUnit

from .models import AccessEvent, VisitorInvitation


class InvitationCreateSerializer(serializers.Serializer):
    visitor_name = serializers.CharField(max_length=180)
    visitor_phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    vehicle_registration = serializers.CharField(max_length=32, required=False, allow_blank=True)
    unit = serializers.PrimaryKeyRelatedField(queryset=ResidentialUnit.objects.all())
    valid_from = serializers.DateTimeField()
    valid_until = serializers.DateTimeField()
    access_type = serializers.ChoiceField(choices=["single_use", "multi_use"])
    max_uses = serializers.IntegerField(min_value=2, max_value=100, required=False)

    def validate(self, attrs):
        if attrs["valid_until"] <= attrs["valid_from"]:
            raise serializers.ValidationError({"valid_until": "Must be later than valid_from."})
        if attrs["access_type"] == "single_use" and attrs.get("max_uses", 1) != 1:
            raise serializers.ValidationError(
                {"max_uses": "Single-use invitations always allow one use."}
            )
        return attrs


class VisitorInvitationSerializer(serializers.ModelSerializer):
    visitor_name = serializers.CharField(source="visitor.full_name", read_only=True)
    visitor_phone = serializers.CharField(source="visitor.phone_number", read_only=True)
    unit_number = serializers.CharField(source="unit.unit_number", read_only=True)

    class Meta:
        model = VisitorInvitation
        fields = [
            "id",
            "visitor_name",
            "visitor_phone",
            "unit",
            "unit_number",
            "valid_from",
            "valid_until",
            "access_type",
            "max_uses",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class CredentialIssuedSerializer(serializers.Serializer):
    invitation = VisitorInvitationSerializer()
    qr_token = serializers.CharField()
    access_code = serializers.CharField()
    qr_payload_format = serializers.CharField(default="opaque-token")


class GateVerifySerializer(serializers.Serializer):
    gate_device = serializers.UUIDField()
    credential = serializers.CharField(max_length=256, trim_whitespace=True)


class GateCheckInSerializer(GateVerifySerializer):
    pass


class GateCheckOutSerializer(serializers.Serializer):
    gate_device = serializers.UUIDField()
    invitation = serializers.UUIDField()


class GateOverrideSerializer(GateCheckOutSerializer):
    reason = serializers.CharField(max_length=500, trim_whitespace=True)


class AccessEventSerializer(serializers.ModelSerializer):
    visitor_name = serializers.CharField(source="invitation.visitor.full_name", read_only=True)

    class Meta:
        model = AccessEvent
        fields = [
            "id",
            "invitation",
            "visitor_name",
            "event_type",
            "status",
            "occurred_at",
            "reason",
            "gate_device",
        ]
        read_only_fields = fields

class GateVerifyResponseSerializer(serializers.Serializer):
    result = serializers.ChoiceField(
        choices=[
            "VALID", "EXPIRED", "CANCELLED", "REVOKED", "ALREADY_USED",
            "NOT_YET_VALID", "INVALID", "ALREADY_CHECKED_IN",
        ]
    )
    visitor_name = serializers.CharField(allow_null=True, required=False)
    unit = serializers.CharField(allow_null=True, required=False)
    valid_until = serializers.DateTimeField(allow_null=True, required=False)
