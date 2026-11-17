import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("estates", "0002_alter_estate_estate_code"),
        ("properties", "0001_initial"),
        ("residents", "0003_residentidentitydocument"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Visitor",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("full_name", models.CharField(max_length=180)),
                ("phone_number", models.CharField(blank=True, max_length=32)),
                ("vehicle_registration", models.CharField(blank=True, max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name="GateDevice",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=120)),
                ("device_identifier", models.CharField(max_length=100)),
                ("status", models.CharField(choices=[("active", "Active"), ("inactive", "Inactive")], default="active", max_length=20)),
                ("estate", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="gate_devices", to="estates.estate")),
            ],
            options={
                "indexes": [models.Index(fields=["estate", "status"], name="access_gate_est_status")],
                "constraints": [models.UniqueConstraint(fields=("estate", "device_identifier"), name="access_gate_device_unique")],
            },
        ),
        migrations.CreateModel(
            name="VisitorInvitation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("valid_from", models.DateTimeField()),
                ("valid_until", models.DateTimeField()),
                ("access_type", models.CharField(choices=[("single_use", "Single use"), ("multi_use", "Multi use")], max_length=20)),
                ("max_uses", models.PositiveSmallIntegerField(default=1)),
                ("status", models.CharField(choices=[("active", "Active"), ("cancelled", "Cancelled"), ("completed", "Completed")], default="active", max_length=20)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_invitations", to=settings.AUTH_USER_MODEL)),
                ("estate", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="visitor_invitations", to="estates.estate")),
                ("resident", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="invitations", to="residents.residentprofile")),
                ("unit", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="visitor_invitations", to="properties.residentialunit")),
                ("visitor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="invitations", to="access_control.visitor")),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["estate", "status", "valid_from"], name="access_inv_est_status"),
                    models.Index(fields=["resident", "-created_at"], name="access_inv_res_created"),
                ],
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("valid_until__gt", models.F("valid_from"))), name="access_invitation_valid_window"),
                    models.CheckConstraint(condition=models.Q(("max_uses__gte", 1), ("max_uses__lte", 100)), name="access_invitation_use_limit"),
                ],
            },
        ),
        migrations.CreateModel(
            name="AccessCredential",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("qr_token_hash", models.CharField(max_length=64, unique=True)),
                ("access_code_hash", models.CharField(max_length=64, unique=True)),
                ("status", models.CharField(choices=[("active", "Active"), ("revoked", "Revoked"), ("consumed", "Consumed")], default="active", max_length=20)),
                ("expires_at", models.DateTimeField()),
                ("uses_count", models.PositiveSmallIntegerField(default=0)),
                ("invitation", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="credential", to="access_control.visitorinvitation")),
            ],
            options={"indexes": [models.Index(fields=["status", "expires_at"], name="access_cred_status_exp")]},
        ),
        migrations.CreateModel(
            name="AccessEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("event_type", models.CharField(choices=[("entry", "Entry"), ("exit", "Exit")], max_length=12)),
                ("status", models.CharField(choices=[("accepted", "Accepted"), ("rejected", "Rejected"), ("overridden", "Administrator override")], max_length=16)),
                ("occurred_at", models.DateTimeField()),
                ("reason", models.CharField(blank=True, max_length=500)),
                ("credential", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="events", to="access_control.accesscredential")),
                ("estate", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="access_events", to="estates.estate")),
                ("gate_device", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="events", to="access_control.gatedevice")),
                ("invitation", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="events", to="access_control.visitorinvitation")),
                ("officer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="access_events", to=settings.AUTH_USER_MODEL)),
                ("related_entry", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="exit_events", to="access_control.accessevent")),
            ],
            options={
                "ordering": ["-occurred_at"],
                "indexes": [
                    models.Index(fields=["estate", "-occurred_at"], name="access_event_est_time"),
                    models.Index(fields=["invitation", "event_type", "status"], name="access_event_inv_type"),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("event_type", "entry"), ("related_entry__isnull", True))
                        | models.Q(("event_type", "exit"), ("related_entry__isnull", False)),
                        name="access_event_exit_requires_entry",
                    )
                ],
            },
        ),
    ]
