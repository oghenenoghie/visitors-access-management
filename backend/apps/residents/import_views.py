from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import has_estate_role
from apps.estates.models import Estate, EstateRole

from .bulk_import import process_bulk_import
from .import_serializers import BulkImportResultSerializer, BulkImportSerializer


class BulkImportView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=BulkImportSerializer,
        responses={200: BulkImportResultSerializer, 201: BulkImportResultSerializer},
    )
    def post(self, request, import_type):
        serializer = BulkImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        estate_id = serializer.validated_data["estate_id"]
        if not has_estate_role(
            request.user, [EstateRole.ESTATE_ADMIN], estate_id=estate_id
        ):
            raise NotFound()
        estate = get_object_or_404(Estate, pk=estate_id)
        result = process_bulk_import(
            estate=estate,
            import_type=import_type,
            uploaded_file=serializer.validated_data["file"],
            dry_run=serializer.validated_data["dry_run"],
            actor=request.user,
            request=request,
        )
        status_code = 200 if serializer.validated_data["dry_run"] else 201
        return Response(result, status=status_code)
