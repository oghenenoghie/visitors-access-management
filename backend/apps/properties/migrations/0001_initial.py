# Generated for M3 property and residential-unit foundations.
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [("estates", "0002_alter_estate_estate_code")]

    operations = [
        migrations.CreateModel(
            name="Property",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=160)),
                ("property_type", models.CharField(choices=[("street", "Street"), ("block", "Block"), ("building", "Building"), ("compound", "Compound")], max_length=20)),
                ("description", models.CharField(blank=True, max_length=500)),
                ("status", models.CharField(choices=[("active", "Active"), ("inactive", "Inactive")], default="active", max_length=20)),
                ("estate", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="properties", to="estates.estate")),
                ("parent", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="children", to="properties.property")),
            ],
            options={"ordering": ["name"], "indexes": [models.Index(fields=["estate", "property_type", "status"], name="properties_estate_type_status")], "constraints": [models.UniqueConstraint(fields=("estate", "parent", "name"), name="properties_parent_name_unique")]},
        ),
        migrations.CreateModel(
            name="ResidentialUnit",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("unit_number", models.CharField(max_length=40)),
                ("floor", models.CharField(blank=True, max_length=30)),
                ("block", models.CharField(blank=True, max_length=40)),
                ("status", models.CharField(choices=[("active", "Active"), ("inactive", "Inactive")], default="active", max_length=20)),
                ("property", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="residential_units", to="properties.property")),
            ],
            options={"ordering": ["property__name", "block", "unit_number"], "indexes": [models.Index(fields=["property", "status"], name="properties_unit_status")], "constraints": [models.UniqueConstraint(fields=("property", "block", "unit_number"), name="properties_unit_location_unique")]},
        ),
    ]
