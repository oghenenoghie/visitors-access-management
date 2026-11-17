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
        read_only_fields = fields
