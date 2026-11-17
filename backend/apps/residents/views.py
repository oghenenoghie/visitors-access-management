from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.common.permissions import administered_estate_ids, has_estate_role
from apps.estates.models import EstateRole

from .models import ResidentProfile
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
        return Response(
            ResidentProfileSerializer(profile).data, status=status.HTTP_201_CREATED
        )


class ResidentViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
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
        queryset = ResidentProfile.objects.select_related(
            "user", "estate", "reviewed_by"
        )
        if user.is_platform_admin:
            return queryset
        if has_estate_role(user, [EstateRole.ESTATE_ADMIN]):
            return queryset.filter(estate_id__in=administered_estate_ids(user))
        return queryset.filter(user=user)

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

    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        return self._review(request, self.get_object(), suspend_resident)
