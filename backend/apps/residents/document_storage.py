import hashlib
import uuid
from pathlib import Path
from io import BytesIO

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.exceptions import SuspiciousOperation

from apps.audit_logs.services import record

from .models import ResidentDocumentStatus, ResidentIdentityDocument


def _master_cipher():
    return Fernet(settings.FIELD_ENCRYPTION_KEY.encode("ascii"))


def store_identity_document(*, resident, uploaded_file, document_type, uploaded_by, request):
    plaintext = uploaded_file.read()
    data_key = Fernet.generate_key()
    ciphertext = Fernet(data_key).encrypt(plaintext)
    wrapped_key = _master_cipher().encrypt(data_key).decode("ascii")
    suffix = Path(uploaded_file.name.replace("\\", "/")).suffix.lower()
    storage_path = (
        f"private/resident-documents/{resident.estate_id}/{resident.pk}/{uuid.uuid4().hex}{suffix}.enc"
    )
    stored_path = default_storage.save(storage_path, ContentFile(ciphertext))
    try:
        document = ResidentIdentityDocument.objects.create(
            resident=resident,
            document_type=document_type,
            original_filename=Path(uploaded_file.name.replace("\\", "/")).name[:255],
            content_type=uploaded_file.validated_content_type,
            size_bytes=len(plaintext),
            sha256=hashlib.sha256(plaintext).hexdigest(),
            storage_key=stored_path,
            wrapped_data_key=wrapped_key,
            uploaded_by=uploaded_by,
        )
    except Exception:
        default_storage.delete(stored_path)
        raise

    record(
        action="resident.identity_document_uploaded",
        actor=uploaded_by,
        estate=resident.estate,
        resource=document,
        new_values={
            "document_type": document_type,
            "size_bytes": len(plaintext),
            "sha256": document.sha256,
        },
        request=request,
    )
    return document


def read_identity_document(document):
    try:
        encrypted = default_storage.open(document.storage_key, "rb").read()
        data_key = _master_cipher().decrypt(document.wrapped_data_key.encode("ascii"))
        plaintext = Fernet(data_key).decrypt(encrypted)
    except (InvalidToken, OSError, ValueError) as exc:
        raise SuspiciousOperation("The stored identity document failed integrity checks.") from exc

    if hashlib.sha256(plaintext).hexdigest() != document.sha256:
        raise SuspiciousOperation("The stored identity document failed integrity checks.")
    return BytesIO(plaintext)
