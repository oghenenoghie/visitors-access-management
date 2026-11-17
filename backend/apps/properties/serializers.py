from rest_framework import serializers

from apps.estates.models import Estate

from .models import Property, ResidentialUnit


class PropertySerializer(serializers.ModelSerializer):
    estate_id = serializers.PrimaryKeyRelatedField(source="estate", queryset=Estate.objects.all())
    parent_id = serializers.PrimaryKeyRelatedField(
        source="parent", queryset=Property.objects.all(), allow_null=True, required=False, default=None
    )

    class Meta:
        model = Property
        fields = [
            "id",
            "estate_id",
            "parent_id",
            "name",
            "property_type",
            "description",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        estate = attrs.get("estate", getattr(self.instance, "estate", None))
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        if self.instance and estate and estate.pk != self.instance.estate_id:
            raise serializers.ValidationError(
                {"estate_id": "A property cannot be moved to another estate."}
            )
        if parent and self.instance and parent.pk == self.instance.pk:
            raise serializers.ValidationError({"parent_id": "A property cannot be its own parent."})
        if parent and estate and parent.estate_id != estate.id:
            raise serializers.ValidationError(
                {"parent_id": "The parent property must belong to the selected estate."}
            )
        return attrs


class ResidentialUnitSerializer(serializers.ModelSerializer):
    estate_id = serializers.UUIDField(source="property.estate_id", read_only=True)
    property_id = serializers.PrimaryKeyRelatedField(
        source="property", queryset=Property.objects.all()
    )

    def validate_property_id(self, value):
        if self.instance and value.estate_id != self.instance.property.estate_id:
            raise serializers.ValidationError(
                "A residential unit cannot be moved to another estate."
            )
        return value

    class Meta:
        model = ResidentialUnit
        fields = [
            "id",
            "estate_id",
            "property_id",
            "unit_number",
            "floor",
            "block",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "estate_id", "created_at", "updated_at"]
