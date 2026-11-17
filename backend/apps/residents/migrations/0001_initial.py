# Generated for M3 resident registration and approval.
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("estates", "0002_alter_estate_estate_code"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ResidentProfile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(choices=[("pending", "Pending approval"), ("approved", "Approved"), ("rejected", "Rejected"), ("suspended", "Suspended")], default="pending", max_length=20)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("review_note", models.CharField(blank=True, max_length=500)),
                ("estate", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="resident_profiles", to="estates.estate")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_resident_profiles", to=settings.AUTH_USER_MODEL)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="resident_profiles", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-submitted_at"], "indexes": [models.Index(fields=["estate", "status"], name="residents_estate_status"), models.Index(fields=["user", "status"], name="residents_user_status")], "constraints": [models.UniqueConstraint(fields=("user", "estate"), name="residents_user_estate_unique")]},
        ),
    ]
