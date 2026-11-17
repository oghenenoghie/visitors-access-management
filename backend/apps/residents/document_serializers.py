from pathlib import Path

from rest_framework import serializers

from .models import ResidentDocumentType, ResidentIdentityDocument

MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
ALLOWED_SIGNATURES = {
    ".pdf": (b"%PDF-", "application/pdf"),
    ".jpg": (b"\xff\xd8\xff", "image/jpeg"),
    ".jpeg": (b"\xff\xd8\xff", "image/jpeg"),
    ".png": (b"\x89PNG\r\n\x1a\n", "image/png"),
}


class ResidentDocumentUploadSerializer(serializers.Serializer):
    document_type = serializers.ChoiceField(choices=ResidentDocumentType.choices)
    file = serializers.FileField(write_only=True)

    def validate_file(self, uploaded_file):
        if uploaded_file.size <= 0 or uploaded_file.size > MAX_DOCUMENT_BYTES:
            raise serializers.ValidationError("The document must be between 1 byte and 10 MB.")
        filename = uploaded_file.name.replace("\\", "/")
        extension = Path(filename).suffix.lower()
        signature = ALLOWED_SIGNATURES.get(extension)
        if signature is None:
            raise serializers.ValidationError("Only PDF, JPEG and PNG files are accepted.")
        header = uploaded_file.read(16)
        uploaded_file.seek(0)
        expected_signature, content_type = signature
        if not header.startswith(expected_signature):
            raise serializers.ValidationError("The file content does not match its extension.")
        uploaded_file.validated_content_type = content_type
        return uploaded_file


class ResidentIdentityDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResidentIdentityDocument
        fields = [
            "id", "document_type", "status", "original_filename", "content_type",
            "size_bytes", "sha256", "created_at",
        ]
        read_only_fields = fields
