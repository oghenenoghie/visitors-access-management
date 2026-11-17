from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ResidentRegistrationView, ResidentViewSet

router = DefaultRouter()
router.register("residents", ResidentViewSet, basename="resident")

urlpatterns = [
    path("residents/register/", ResidentRegistrationView.as_view(), name="resident-register"),
    *router.urls,
]
