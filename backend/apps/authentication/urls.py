from django.urls import path

from . import views

urlpatterns = [
    path("auth/login/", views.LoginView.as_view(), name="auth-login"),
    path("auth/logout/", views.LogoutView.as_view(), name="auth-logout"),
    path(
        "auth/token/refresh/",
        views.LockedTokenRefreshView.as_view(),
        name="auth-token-refresh",
    ),
    path("auth/me/", views.MeView.as_view(), name="auth-me"),
    path("auth/password/reset/", views.PasswordResetView.as_view(), name="auth-password-reset"),
    path("auth/2fa/setup/", views.TwoFactorSetupView.as_view(), name="auth-2fa-setup"),
    path("auth/2fa/confirm/", views.TwoFactorConfirmView.as_view(), name="auth-2fa-confirm"),
    path("auth/2fa/verify/", views.TwoFactorVerifyView.as_view(), name="auth-2fa-verify"),
    path(
        "admin/users/<uuid:pk>/password-reset/",
        views.IssuePasswordResetView.as_view(),
        name="admin-user-password-reset",
    ),
    path(
        "admin/users/<uuid:pk>/two-factor-reset/",
        views.ResetTwoFactorView.as_view(),
        name="admin-user-two-factor-reset",
    ),
]
