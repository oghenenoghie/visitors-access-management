# Generated for encrypted resident identity document metadata.
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("residents", "0002_residentunitassignment"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ResidentIdentityDocument",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("document_type", models.CharField(choices=[("national_id", "National identity card"), ("passport", "Passport"), ("drivers_license", "Driver's licence"), ("other", "Other approved identity document")], max_length=24)),
                ("status", models.CharField(choices=[("active", "Active"), ("archived", "Archived")], default="active", max_length=20)),
                ("original_filename", models.CharField(max_length=255)),
                ("content_type", models.CharField(max_length=100)),
                ("size_bytes", models.PositiveIntegerField()),
                ("sha256", models.CharField(max_length=64)),
                ("storage_key", models.CharField(max_length=500)),
                ("wrapped_data_key", models.TextField()),
                ("resident", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="identity_documents", to="residents.residentprofile")),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="uploaded_resident_documents", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["resident", "status"], name="resident_docs_status"),
                ],
            },
        ),
    ]
