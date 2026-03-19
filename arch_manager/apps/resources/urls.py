from django.urls import path

from . import views

app_name = "resources"

urlpatterns = [
    path("", views.ResourceListView.as_view(), name="list"),
    path("new/", views.resource_create, name="create"),
    path("type/", views.resource_type_list, name="type-list"),
    path("type/new/", views.resource_type_create, name="type-create"),
    path("type/<slug:slug>/edit/", views.resource_type_update, name="type-update"),
    path("type/<slug:type_slug>/", views.ResourceByTypeListView.as_view(), name="by-type"),
    path("<slug:slug>/", views.ResourceDetailView.as_view(), name="detail"),
    path("<slug:slug>/edit/", views.resource_update, name="update"),
]
