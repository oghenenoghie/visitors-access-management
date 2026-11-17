from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    estate_id = serializers.UUIDField(read_only=True, allow_null=True)
    actor_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "created_at",
            "estate_id",
            "actor_id",
            "actor_email",
            "action",
            "resource_type",
            "resource_id",
            "previous_values",
            "new_values",
            "ip_address",
            "user_agent",
        ]
        read_only_fields = fields
