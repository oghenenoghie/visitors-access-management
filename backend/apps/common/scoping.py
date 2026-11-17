"""Estate isolation.

Every estate-owned queryset is scoped through ``for_user``. A caller sees only rows
belonging to estates in which they hold an active membership. Platform administrators
see all estates (cross-estate reads must be audited once the audit log exists, M2).
Anonymous or inactive callers see nothing.
"""

from django.db import models


def active_estate_ids(user):
    """Estate ids in which ``user`` holds an active membership of an active estate."""
    from apps.estates.models import EstateMembership

    return EstateMembership.objects.active().filter(user=user).values("estate_id")


class EstateScopedQuerySet(models.QuerySet):
    # Lookup path from this model to the estate id. Estate itself overrides it to "id".
    estate_lookup = "estate_id"

    def for_user(self, user):
        if user is None or not user.is_authenticated or not user.is_active:
            return self.none()
        if user.is_platform_admin:
            return self.all()
        return self.filter(**{f"{self.estate_lookup}__in": active_estate_ids(user)})
