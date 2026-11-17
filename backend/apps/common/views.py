from django.db import OperationalError, connection
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@extend_schema(
    responses=inline_serializer(
        "Health",
        {"status": serializers.CharField(), "database": serializers.CharField()},
    ),
    auth=[],
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health(request):
    """Liveness and database check. Exposes no sensitive information."""
    try:
        connection.ensure_connection()
        database = "ok"
    except OperationalError:
        database = "unavailable"
    healthy = database == "ok"
    return Response(
        {"status": "ok" if healthy else "degraded", "database": database},
        status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
    )
