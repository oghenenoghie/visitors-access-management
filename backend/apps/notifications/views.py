from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import DeviceRegistrationSerializer, NotificationSerializer
from .services import deactivate_device, register_device


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=NotificationSerializer)
    def post(self, request, pk):
        notification = get_object_or_404(Notification.objects.filter(user=request.user), pk=pk)
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at", "updated_at"])
        return Response(NotificationSerializer(notification).data)


class DeviceRegistrationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=DeviceRegistrationSerializer,
        responses={
            200: inline_serializer(
                name="DeviceRegistrationResponse",
                fields={"registered": serializers.BooleanField()},
            )
        },
    )
    def post(self, request):
        serializer = DeviceRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = register_device(
            user=request.user,
            token=serializer.validated_data["token"],
            platform=serializer.validated_data["platform"],
        )
        return Response({"registered": device.is_active}, status=status.HTTP_200_OK)

    @extend_schema(
        request=DeviceRegistrationSerializer,
        responses={204: None},
    )
    def delete(self, request):
        serializer = DeviceRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deactivate_device(user=request.user, token=serializer.validated_data["token"])
        return Response(status=status.HTTP_204_NO_CONTENT)
