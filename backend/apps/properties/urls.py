from rest_framework.routers import DefaultRouter

from .views import PropertyViewSet, ResidentialUnitViewSet

router = DefaultRouter()
router.register("properties", PropertyViewSet, basename="property")
router.register("residential-units", ResidentialUnitViewSet, basename="residential-unit")

urlpatterns = router.urls
