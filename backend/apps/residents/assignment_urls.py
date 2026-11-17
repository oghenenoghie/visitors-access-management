from rest_framework.routers import DefaultRouter

from .assignment_views import ResidentUnitAssignmentViewSet

router = DefaultRouter()
router.register(
    "resident-unit-assignments",
    ResidentUnitAssignmentViewSet,
    basename="resident-unit-assignment",
)

urlpatterns = router.urls
