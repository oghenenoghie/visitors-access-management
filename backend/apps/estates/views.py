from rest_framework import viewsets

from .models import Estate
from .serializers import EstateSerializer


class EstateViewSet(viewsets.ReadOnlyModelViewSet):
    """Estates the caller belongs to. Write access arrives with role permissions (M2)."""

    serializer_class = EstateSerializer
    queryset = Estate.objects.none()  # replaced per request; keeps schema generation working
    search_fields = ["name", "estate_code"]

    def get_queryset(self):
        return Estate.objects.for_user(self.request.user).order_by("name")
