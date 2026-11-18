from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import has_estate_role
from apps.estates.models import EstateRole

from .models import AccessEvent, VisitorInvitation
from .permissions import CanOverrideAccess, GateAttemptThrottle, GateRolePermission
from .serializers import (
    AccessEventSerializer,
    GateCheckInSerializer,
    GateCheckOutSerializer,
    GateOverrideSerializer,
    GateVerifyResponseSerializer,
    GateVerifySerializer,
    InvitationCreateSerializer,
    VisitorInvitationSerializer,
)
from .services import (
    _gate_for_actor,
    cancel_invitation,
    check_in,
    check_out,
    create_invitation,
    manual_override,
    verify_credential,
)


class InvitationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VisitorInvitation.objects.none()
        user = self.request.user
        qs = VisitorInvitation.objects.for_user(user).select_related(
            "visitor", "resident", "unit", "estate", "created_by"
        )
        if user.is_platform_admin:
            return qs
        admin_estates = user.memberships.filter(
            role=EstateRole.ESTATE_ADMIN, status="active", estate__status="active"
        ).values("estate_id")
        if has_estate_role(user, [EstateRole.ESTATE_ADMIN]):
            return qs.filter(estate_id__in=admin_estates)
        return qs.filter(created_by=user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return InvitationCreateSerializer
        return VisitorInvitationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation, _credential, qr_token, access_code = create_invitation(
            actor=request.user, data=serializer.validated_data, request=request
        )
        payload = {
            "invitation": VisitorInvitationSerializer(invitation).data,
            "qr_token": qr_token,
            "access_code": access_code,
            "qr_payload_format": "opaque-token",
        }
        return Response(payload, status=status.HTTP_201_CREATED)


class InvitationDetailView(generics.RetrieveAPIView):
    serializer_class = VisitorInvitationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VisitorInvitation.objects.none()
        user = self.request.user
        queryset = VisitorInvitation.objects.for_user(user).select_related(
            "visitor", "resident", "unit", "estate", "created_by"
        )
        if user.is_platform_admin:
            return queryset
        if has_estate_role(user, [EstateRole.ESTATE_ADMIN]):
            estate_ids = user.memberships.filter(
                role=EstateRole.ESTATE_ADMIN, status="active", estate__status="active"
            ).values("estate_id")
            return queryset.filter(estate_id__in=estate_ids)
        return queryset.filter(created_by=user)


class InvitationCancelView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={200: VisitorInvitationSerializer})
    def post(self, request, pk):
        invitation = get_object_or_404(VisitorInvitation.objects.for_user(request.user), pk=pk)
        if (
            invitation.created_by_id != request.user.pk
            and not has_estate_role(
                request.user, [EstateRole.ESTATE_ADMIN], estate_id=invitation.estate_id
            )
            and not request.user.is_platform_admin
        ):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "Only the creator or an estate administrator may cancel this invitation."
            )
        invitation = cancel_invitation(invitation=invitation, actor=request.user, request=request)
        return Response(VisitorInvitationSerializer(invitation).data)


class GateVerifyView(APIView):
    throttle_classes = [GateAttemptThrottle]
    permission_classes = [IsAuthenticated, GateRolePermission]

    @extend_schema(request=GateVerifySerializer, responses={200: GateVerifyResponseSerializer})
    def post(self, request):
        serializer = GateVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        gate = _gate_for_actor(
            actor=request.user,
            gate_id=serializer.validated_data["gate_device"],
            allowed_roles=GateRolePermission.allowed_roles,
        )
        result, _ = verify_credential(
            value=serializer.validated_data["credential"],
            gate=gate,
            actor=request.user,
            request=request,
        )
        return Response(result)


class GateCheckInView(APIView):
    throttle_classes = [GateAttemptThrottle]
    permission_classes = [IsAuthenticated, GateRolePermission]

    @extend_schema(request=GateCheckInSerializer, responses={201: AccessEventSerializer})
    def post(self, request):
        serializer = GateCheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        gate = _gate_for_actor(
            actor=request.user,
            gate_id=serializer.validated_data["gate_device"],
            allowed_roles=GateRolePermission.allowed_roles,
        )
        event = check_in(
            value=serializer.validated_data["credential"],
            gate=gate,
            actor=request.user,
            request=request,
        )
        return Response(AccessEventSerializer(event).data, status=status.HTTP_201_CREATED)


class GateCheckOutView(APIView):
    permission_classes = [IsAuthenticated, GateRolePermission]

    @extend_schema(request=GateCheckOutSerializer, responses={201: AccessEventSerializer})
    def post(self, request):
        serializer = GateCheckOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        gate = _gate_for_actor(
            actor=request.user,
            gate_id=serializer.validated_data["gate_device"],
            allowed_roles=GateRolePermission.allowed_roles,
        )
        invitation = get_object_or_404(
            VisitorInvitation.objects.for_user(request.user),
            pk=serializer.validated_data["invitation"],
            estate=gate.estate,
        )
        event = check_out(invitation=invitation, gate=gate, actor=request.user, request=request)
        return Response(AccessEventSerializer(event).data, status=status.HTTP_201_CREATED)


class GateOverrideView(APIView):
    permission_classes = [IsAuthenticated, CanOverrideAccess]

    @extend_schema(request=GateOverrideSerializer, responses={201: AccessEventSerializer})
    def post(self, request):
        serializer = GateOverrideSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        gate = _gate_for_actor(
            actor=request.user,
            gate_id=serializer.validated_data["gate_device"],
            allowed_roles=[EstateRole.SECURITY_SUPERVISOR, EstateRole.ESTATE_ADMIN],
        )
        invitation = get_object_or_404(
            VisitorInvitation.objects.for_user(request.user),
            pk=serializer.validated_data["invitation"],
            estate=gate.estate,
        )
        event = manual_override(
            invitation=invitation,
            gate=gate,
            actor=request.user,
            reason=serializer.validated_data["reason"],
            request=request,
        )
        return Response(AccessEventSerializer(event).data, status=status.HTTP_201_CREATED)


class GateActivityView(generics.ListAPIView):
    serializer_class = AccessEventSerializer
    permission_classes = [IsAuthenticated, GateRolePermission]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return AccessEvent.objects.none()
        user = self.request.user
        queryset = AccessEvent.objects.all()
        if not user.is_platform_admin:
            queryset = queryset.filter(
                estate_id__in=user.memberships.filter(
                    role__in=GateRolePermission.allowed_roles,
                    status="active",
                    estate__status="active",
                ).values("estate_id")
            )
        return queryset.select_related("invitation__visitor", "gate_device").order_by(
            "-occurred_at"
        )
