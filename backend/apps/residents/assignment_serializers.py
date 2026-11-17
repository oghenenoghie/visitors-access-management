from rest_framework import serializers

from apps.properties.models import ResidentialUnit

from .assignments import AssignmentRelationship, ResidentUnitAssignment
from .models import ResidentProfile


class ResidentUnitAssignmentCreateSerializer(serializers.Serializer):
    resident_id = serializers.PrimaryKeyRelatedField(
        source="resident", queryset=ResidentProfile.objects.all()
    )
    unit_id = serializers.PrimaryKeyRelatedField(
        source="unit", queryset=ResidentialUnit.objects.all()
    )
    relationship = serializers.ChoiceField(choices=AssignmentRelationship.choices)
    is_primary = serializers.BooleanField(default=False)
    starts_on = serializers.DateField()
    ends_on = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        if attrs.get("ends_on") and attrs["ends_on"] < attrs["starts_on"]:
            raise serializers.ValidationError(
                {"ends_on": "End date cannot precede start date."}
            )
        if attrs["resident"].estate_id != attrs["unit"].property.estate_id:
            raise serializers.ValidationError(
                {"unit_id": "The unit must belong to the resident's estate."}
            )
        return attrs


class AssignmentEndSerializer(serializers.Serializer):
    ends_on = serializers.DateField()


class ResidentUnitAssignmentSerializer(serializers.ModelSerializer):
    resident_id = serializers.UUIDField(source="resident_id", read_only=True)
    resident_email = serializers.EmailField(source="resident.user.email", read_only=True)
    unit_id = serializers.UUIDField(read_only=True)
    unit_number = serializers.CharField(source="unit.unit_number", read_only=True)
    estate_id = serializers.UUIDField(source="resident.estate_id", read_only=True)

    class Meta:
        model = ResidentUnitAssignment
        fields = [
            "id", "resident_id", "resident_email", "estate_id", "unit_id", "unit_number",
            "relationship", "status", "is_primary", "starts_on", "ends_on",
            "created_at", "updated_at",
        ]
        read_only_fields = fields
