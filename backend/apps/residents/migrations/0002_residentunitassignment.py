# Generated for M3 resident-to-unit assignments.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("properties", "0001_initial"),
        ("residents", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResidentUnitAssignment",
            fields=[
                ("id", models.UUIDField(default=__import__("uuid").uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("relationship", models.CharField(choices=[("owner", "Owner"), ("tenant", "Tenant"), ("occupant", "Occupant")], max_length=20)),
                ("status", models.CharField(choices=[("active", "Active"), ("ended", "Ended")], default="active", max_length=20)),
                ("is_primary", models.BooleanField(default=False)),
                ("starts_on", models.DateField()),
                ("ends_on", models.DateField(blank=True, null=True)),
                ("resident", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="unit_assignments", to="residents.residentprofile")),
                ("unit", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="resident_assignments", to="properties.residentialunit")),
            ],
            options={
                "ordering": ["-starts_on", "-created_at"],
                "indexes": [
                    models.Index(fields=["resident", "status"], name="residents_assignment_status"),
                    models.Index(fields=["unit", "status"], name="units_assignment_status"),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("ends_on__isnull", True), ("ends_on__gte", models.F("starts_on")), _connector="OR"),
                        name="residents_assignment_valid_dates",
                    ),
                    models.UniqueConstraint(
                        fields=("resident",),
                        condition=models.Q(("is_primary", True), ("status", "active")),
                        name="residents_one_active_primary_unit",
                    ),
                ],
            },
        ),
    ]
