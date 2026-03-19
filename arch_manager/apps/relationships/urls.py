from django.urls import path

from . import views

app_name = "relationships"

urlpatterns = [
    path("new/<slug:resource_slug>/", views.relationship_create, name="create-for-resource"),
    path("new/", views.relationship_create, name="create"),
    path("<int:pk>/edit/", views.relationship_update, name="update"),
    path("<int:pk>/delete/", views.relationship_delete, name="delete"),
]
