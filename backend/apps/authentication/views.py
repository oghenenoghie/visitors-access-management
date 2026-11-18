from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from apps.common.permissions import IsAdministrator, administrable_users
from apps.users.models import User

from . import services
from .serializers import (
    AuthResponseSerializer,
    ChallengeCodeSerializer,
    ChallengeSerializer,
    EnrolmentResponseSerializer,
    LockedTokenRefreshSerializer,
    LoginSerializer,
    LogoutSerializer,
    MeSerializer,
    PasswordResetRedeemSerializer,
    ResetCodeIssuedSerializer,
)


class _PublicView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]


class LoginView(_PublicView):
    throttle_scope = "login"

    @extend_schema(request=LoginSerializer, responses=AuthResponseSerializer, auth=[])
    def post(self, request):
        data = LoginSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        result = services.login(
            email=data.validated_data["email"],
            password=data.validated_data["password"],
            request=request,
        )
        return Response(result)


class LockedTokenRefreshView(TokenRefreshView):
    """Refresh with database-backed serialization shared by every API worker."""

    serializer_class = LockedTokenRefreshSerializer


class TwoFactorSetupView(_PublicView):
    throttle_scope = "two_factor"

    @extend_schema(request=ChallengeSerializer, responses=EnrolmentResponseSerializer, auth=[])
    def post(self, request):
        data = ChallengeSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(
            services.start_enrolment(
                challenge_token=data.validated_data["challenge_token"], request=request
            )
        )


class TwoFactorConfirmView(_PublicView):
    throttle_scope = "two_factor"

    @extend_schema(request=ChallengeCodeSerializer, responses=AuthResponseSerializer, auth=[])
    def post(self, request):
        data = ChallengeCodeSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(
            services.confirm_enrolment(
                challenge_token=data.validated_data["challenge_token"],
                code=data.validated_data["code"],
                request=request,
            )
        )


class TwoFactorVerifyView(_PublicView):
    throttle_scope = "two_factor"

    @extend_schema(request=ChallengeCodeSerializer, responses=AuthResponseSerializer, auth=[])
    def post(self, request):
        data = ChallengeCodeSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(
            services.verify_two_factor(
                challenge_token=data.validated_data["challenge_token"],
                code=data.validated_data["code"],
                request=request,
            )
        )


class PasswordResetView(_PublicView):
    """Redeem an administrator-issued reset code and set a new password."""

    throttle_scope = "password_reset"

    @extend_schema(request=PasswordResetRedeemSerializer, responses={204: None}, auth=[])
    def post(self, request):
        data = PasswordResetRedeemSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        services.redeem_reset_code(request=request, **data.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=LogoutSerializer, responses={204: None})
    def post(self, request):
        data = LogoutSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        services.logout(
            refresh_token=data.validated_data["refresh"], user=request.user, request=request
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=MeSerializer)
    def get(self, request):
        user = User.objects.prefetch_related("memberships__estate").get(pk=request.user.pk)
        return Response(MeSerializer(user).data)


class _AdminUserActionView(APIView):
    permission_classes = [IsAdministrator]

    def get_target(self, request, pk):
        # Out-of-scope users are 404, not 403, so existence is not revealed.
        return get_object_or_404(administrable_users(request.user), pk=pk)


class IssuePasswordResetView(_AdminUserActionView):
    @extend_schema(request=None, responses={201: ResetCodeIssuedSerializer})
    def post(self, request, pk):
        target = self.get_target(request, pk)
        code, expires_at = services.issue_reset_code(
            target=target, actor=request.user, request=request
        )
        return Response({"code": code, "expires_at": expires_at}, status=status.HTTP_201_CREATED)


class ResetTwoFactorView(_AdminUserActionView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request, pk):
        target = self.get_target(request, pk)
        services.reset_two_factor(target=target, actor=request.user, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)
