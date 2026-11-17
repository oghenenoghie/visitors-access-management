import hashlib

import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.audit_logs.models import AuditLog
from apps.estates.models import EstateRole
from apps.residents.models import ResidentIdentityDocument, ResidentProfile

pytestmark = pytest.mark.django_db

REGISTER = "/api/v1/residents/register/"
RESIDENTS = "/api/v1/residents/"


def test_registration_encrypts_optional_identity_document(api_client, make_estate):
    estate = make_estate()
    raw = b"%PDF-1.7\nprivate resident identity data"
    upload = SimpleUploadedFile("identity.pdf", raw, content_type="application/pdf")
    response = api_client.post(
        REGISTER,
        {
            "estate_code": estate.estate_code,
            "email": "document.resident@example.com",
            "password": "A-strong-resident-passw0rd!",
            "first_name": "Document",
            "last_name": "Resident",
            "identity_document_type": "passport",
            "identity_document": upload,
        },
        format="multipart",
    )

    assert response.status_code == 201
    profile = ResidentProfile.objects.get(user__email="document.resident@example.com")
    document = ResidentIdentityDocument.objects.get(resident=profile)
    with default_storage.open(document.storage_key, "rb") as stored:
        encrypted = stored.read()
    assert encrypted != raw
    assert document.sha256 == hashlib.sha256(raw).hexdigest()
    assert document.wrapped_data_key
    assert "storage_key" not in response.json()
    default_storage.delete(document.storage_key)


def test_estate_admin_can_list_and_download_identity_document(
    api_client, auth, make_estate, make_member
):
    estate = make_estate()
    admin = make_member(estate, EstateRole.ESTATE_ADMIN)
    raw = b"%PDF-1.7\nprivate resident identity data"
    upload = SimpleUploadedFile("identity.pdf", raw, content_type="application/pdf")
    response = api_client.post(
        REGISTER,
        {
            "estate_code": estate.estate_code,
            "email": "download.resident@example.com",
            "password": "A-strong-resident-passw0rd!",
            "first_name": "Download",
            "last_name": "Resident",
            "identity_document_type": "national_id",
            "identity_document": upload,
        },
        format="multipart",
    )
    assert response.status_code == 201
    profile = ResidentProfile.objects.get(user__email="download.resident@example.com")
    document = ResidentIdentityDocument.objects.get(resident=profile)
    auth(admin)

    listed = api_client.get(f"{RESIDENTS}{profile.pk}/documents/")
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == str(document.pk)
    downloaded = api_client.get(
        f"{RESIDENTS}{profile.pk}/documents/{document.pk}/download/"
    )
    assert downloaded.status_code == 200
    assert b"".join(downloaded.streaming_content) == raw
    assert AuditLog.objects.filter(
        action="resident.identity_document_viewed", actor=admin, resource_id=str(document.pk)
    ).exists()
    default_storage.delete(document.storage_key)


def test_identity_document_rejects_mismatched_file_signature(api_client, make_estate):
    estate = make_estate()
    upload = SimpleUploadedFile("identity.pdf", b"not a PDF", content_type="application/pdf")
    response = api_client.post(
        REGISTER,
        {
            "estate_code": estate.estate_code,
            "email": "bad.document@example.com",
            "password": "A-strong-resident-passw0rd!",
            "first_name": "Bad",
            "last_name": "Document",
            "identity_document_type": "other",
            "identity_document": upload,
        },
        format="multipart",
    )

    assert response.status_code == 400
    assert not ResidentProfile.objects.filter(user__email="bad.document@example.com").exists()
