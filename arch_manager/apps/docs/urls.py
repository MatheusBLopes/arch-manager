from django.urls import path

from . import views

app_name = "docs"

urlpatterns = [
    path("resource/<slug:resource_slug>/edit/", views.documentation_edit, name="edit"),
]
