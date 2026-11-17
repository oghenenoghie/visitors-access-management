from rest_framework import serializers

from .bulk_import import MAX_IMPORT_BYTES


class BulkImportSerializer(serializers.Serializer):
    estate_id = serializers.UUIDField()
    file = serializers.FileField(write_only=True)
    dry_run = serializers.BooleanField(required=False, default=True)

    def validate_file(self, uploaded_file):
        if uploaded_file.size <= 0:
            raise serializers.ValidationError("Upload a non-empty CSV file.")
        if uploaded_file.size > MAX_IMPORT_BYTES:
            raise serializers.ValidationError("CSV file must not exceed 5 MB.")
        if not uploaded_file.name.lower().endswith(".csv"):
            raise serializers.ValidationError("Upload a .csv file.")
        return uploaded_file


class BulkImportResultSerializer(serializers.Serializer):
    import_type = serializers.ChoiceField(choices=["units", "residents"])
    estate_id = serializers.UUIDField()
    dry_run = serializers.BooleanField()
    valid_rows = serializers.IntegerField()
    error_rows = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.JSONField())
    committed = serializers.BooleanField()
