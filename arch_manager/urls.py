"""
URL configuration for arch_manager project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path("", include("arch_manager.apps.core.urls")),
    path("projects/", include("arch_manager.apps.projects.urls")),
    path("resources/", include("arch_manager.apps.resources.urls")),
    path("relationships/", include("arch_manager.apps.relationships.urls")),
    path("docs/", include("arch_manager.apps.docs.urls")),
]

if settings.DEBUG:  # pragma: no cover
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
