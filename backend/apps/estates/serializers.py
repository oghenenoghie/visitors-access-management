from rest_framework import serializers

from .models import Estate


class EstateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estate
        fields = [
            "id",
            "name",
            "estate_code",
            "address",
            "contact_email",
            "contact_phone",
            "timezone",
            "status",
        ]
        read_only_fields = ["id"]

    def validate_estate_code(self, value):
        if self.instance is not None and value != self.instance.estate_code:
            raise serializers.ValidationError("The estate code cannot be changed.")
        return value
