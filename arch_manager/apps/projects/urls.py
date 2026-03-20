from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="list"),
    path("new/", views.project_create, name="create"),
    path("<slug:slug>/", views.ProjectDetailView.as_view(), name="detail"),
    path("<slug:slug>/edit/", views.project_update, name="update"),
    path("<slug:slug>/delete/", views.project_delete, name="delete"),
    path("<slug:slug>/docs/", views.documentation_edit, name="docs-edit"),
]
