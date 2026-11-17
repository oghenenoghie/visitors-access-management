from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.common.urls")),
    path("api/v1/", include("apps.estates.urls")),
    path("api/v1/", include("apps.properties.urls")),
    path("api/v1/", include("apps.residents.urls")),
    path("api/v1/", include("apps.residents.assignment_urls")),
    path("api/v1/", include("apps.authentication.urls")),
    path("api/v1/", include("apps.audit_logs.urls")),
]

if settings.API_DOCS_ENABLED:
    urlpatterns += [
        path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/v1/docs/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="api-docs",
        ),
    ]
