import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("users", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="DeviceRegistration",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, editable=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("token_encrypted", models.TextField()),
                ("platform", models.CharField(choices=[("android", "Android"), ("ios", "iOS")], max_length=12)),
                ("is_active", models.BooleanField(default=True)),
                ("last_seen_at", models.DateTimeField()),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="push_devices", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False, editable=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("notification_type", models.CharField(max_length=64)),
                ("title", models.CharField(max_length=160)),
                ("body", models.CharField(max_length=500)),
                ("data", models.JSONField(blank=True, default=dict)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(model_name="deviceregistration", index=models.Index(fields=["user", "is_active"], name="notif_device_user_active")),
        migrations.AddIndex(model_name="notification", index=models.Index(fields=["user", "-created_at"], name="notif_user_created")),
    ]
