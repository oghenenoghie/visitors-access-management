import uuid

from django.conf import settings
from django.db import models


class AppendOnlyError(Exception):
    pass


class AuditLog(models.Model):
    """Append-only record of security-relevant activity.

    Rows are never updated or deleted: the model refuses, and a database trigger
    (migration 0002) enforces it even for raw SQL. ``actor`` and ``estate`` keep no database
    constraint so that nothing ever needs to rewrite an audit row.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    estate = models.ForeignKey(
        "estates.Estate",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        related_name="+",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        related_name="+",
    )
    actor_email = models.CharField(max_length=254, blank=True)
    action = models.CharField(max_length=64)
    resource_type = models.CharField(max_length=64, blank=True)
    resource_id = models.CharField(max_length=64, blank=True)
    previous_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["estate", "-created_at"], name="audit_estate_created"),
            models.Index(fields=["actor", "-created_at"], name="audit_actor_created"),
            models.Index(fields=["action"], name="audit_action"),
        ]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M:%S} {self.action}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise AppendOnlyError("Audit log entries cannot be modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AppendOnlyError("Audit log entries cannot be deleted.")
