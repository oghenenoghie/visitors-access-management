from django.urls import path

from .views import (
    GateActivityView,
    GateCheckInView,
    GateCheckOutView,
    GateOverrideView,
    GateVerifyView,
    InvitationDetailView,
    InvitationCancelView,
    InvitationListCreateView,
)

urlpatterns = [
    path("invitations/", InvitationListCreateView.as_view(), name="invitation-list-create"),
    path("invitations/<uuid:pk>/", InvitationDetailView.as_view(), name="invitation-detail"),
    path("invitations/<uuid:pk>/cancel/", InvitationCancelView.as_view(), name="invitation-cancel"),
    path("gate/verify/", GateVerifyView.as_view(), name="gate-verify"),
    path("gate/check-in/", GateCheckInView.as_view(), name="gate-check-in"),
    path("gate/check-out/", GateCheckOutView.as_view(), name="gate-check-out"),
    path("gate/override/", GateOverrideView.as_view(), name="gate-override"),
    path("gate/activity/", GateActivityView.as_view(), name="gate-activity"),
]
