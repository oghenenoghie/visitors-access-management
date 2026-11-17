from django.urls import path

from .import_views import BulkImportView

urlpatterns = [
    path("imports/<str:import_type>/", BulkImportView.as_view(), name="bulk-import"),
]
