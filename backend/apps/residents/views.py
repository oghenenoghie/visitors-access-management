from django.http import FileResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.estates.models import EstateMembership, EstateRole

from .document_serializers import (
    ResidentDocumentUploadSerializer,
    ResidentIdentityDocumentSerializer,
)
from .document_storage import read_identity_document, store_identity_document
from .models import ResidentDocumentStatus, ResidentProfile, ResidentStatus
from .permissions import CanManageResidents
from .serializers import (
    ResidentProfileSerializer,
    ResidentRegistrationSerializer,
    ResidentReviewSerializer,
)
from .services import approve_resident, register_resident, reject_resident, suspend_resident


class ResidentRegistrationView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "resident_registration"

    @extend_schema(
        request=ResidentRegistrationSerializer,
        responses={201: ResidentProfileSerializer},
        auth=[],
    )
    def post(self, request):
        serializer = ResidentRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = register_resident(data=serializer.validated_data, request=request)
        return Response(ResidentProfileSerializer(profile).data, status=status.HTTP_201_CREATED)


class ResidentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ResidentProfileSerializer
    queryset = ResidentProfile.objects.none()
    filterset_fields = ["estate", "status"]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "user__phone_number",
    ]
    ordering_fields = ["submitted_at", "reviewed_at", "status"]

    def get_permissions(self):
        if self.action in ("approve", "reject", "suspend"):
            return [CanManageResidents()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        queryset = ResidentProfile.objects.select_related("user", "estate", "reviewed_by")
        if user.is_platform_admin:
            return queryset
        readable_estate_ids = (
            EstateMembership.objects.active()
            .filter(
                user=user,
                role__in=[EstateRole.ESTATE_ADMIN, EstateRole.ESTATE_MANAGER],
            )
            .values("estate_id")
        )
        if readable_estate_ids.exists():
            return queryset.filter(estate_id__in=readable_estate_ids)
        return queryset.filter(user=user, status=ResidentStatus.APPROVED)

    def _review(self, request, profile, service):
        serializer = ResidentReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = service(
            profile=profile,
            actor=request.user,
            request=request,
            note=serializer.validated_data.get("note", ""),
        )
        return Response(self.get_serializer(result).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._review(request, self.get_object(), approve_resident)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._review(request, self.get_object(), reject_resident)

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="documents",
        parser_classes=[MultiPartParser, FormParser],
    )
    def documents(self, request, pk=None):
        profile = self.get_object()
        if request.method == "GET":
            documents = profile.identity_documents.filter(status=ResidentDocumentStatus.ACTIVE)
            return Response(ResidentIdentityDocumentSerializer(documents, many=True).data)

        serializer = ResidentDocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = store_identity_document(
            resident=profile,
            uploaded_file=serializer.validated_data["file"],
            document_type=serializer.validated_data["document_type"],
            uploaded_by=request.user,
            request=request,
        )
        return Response(
            ResidentIdentityDocumentSerializer(document).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path=r"documents/(?P<document_id>[^/.]+)/download",
    )
    def download_document(self, request, pk=None, document_id=None):
        profile = self.get_object()
        document = get_object_or_404(
            profile.identity_documents.filter(status=ResidentDocumentStatus.ACTIVE),
            pk=document_id,
        )
        content = read_identity_document(document)
        from apps.audit_logs.services import record

        record(
            action="resident.identity_document_viewed",
            actor=request.user,
            estate=profile.estate,
            resource=document,
            new_values={"document_type": document.document_type},
            request=request,
        )
        return FileResponse(
            content,
            as_attachment=True,
            filename=document.original_filename,
            content_type=document.content_type,
        )

    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        return self._review(request, self.get_object(), suspend_resident)
