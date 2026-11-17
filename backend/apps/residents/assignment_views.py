from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import administered_estate_ids, has_estate_role
from apps.estates.models import EstateRole

from .assignment_serializers import (
    AssignmentEndSerializer,
    ResidentUnitAssignmentCreateSerializer,
    ResidentUnitAssignmentSerializer,
)
from .assignment_services import create_assignment, end_assignment
from .assignments import ResidentUnitAssignment
from .permissions import CanManageResidents


class ResidentUnitAssignmentViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    queryset = ResidentUnitAssignment.objects.none()
    filterset_fields = ["resident", "unit", "status", "relationship", "is_primary"]
    search_fields = ["resident__user__email", "resident__user__first_name", "unit__unit_number"]
    ordering_fields = ["starts_on", "ends_on", "created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return ResidentUnitAssignmentCreateSerializer
        return ResidentUnitAssignmentSerializer

    def get_permissions(self):
        if self.action in ("create", "end"):
            return [CanManageResidents()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        queryset = ResidentUnitAssignment.objects.select_related(
            "resident__user", "resident__estate", "unit", "unit__property"
        )
        if user.is_platform_admin:
            return queryset
        if has_estate_role(user, [EstateRole.ESTATE_ADMIN]):
            return queryset.filter(
                resident__estate_id__in=administered_estate_ids(user)
            )
        return queryset.filter(resident__user=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        assignment = create_assignment(
            **data,
            actor=request.user,
            request=request,
        )
        return Response(
            ResidentUnitAssignmentSerializer(assignment).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        assignment = self.get_object()
        serializer = AssignmentEndSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = end_assignment(
            assignment=assignment,
            ends_on=serializer.validated_data["ends_on"],
            actor=request.user,
            request=request,
        )
        return Response(ResidentUnitAssignmentSerializer(assignment).data)
