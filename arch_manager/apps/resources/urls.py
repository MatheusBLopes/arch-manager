from django.urls import path

from . import views

app_name = "resources"

urlpatterns = [
    path("", views.ResourceListView.as_view(), name="list"),
    path("new/", views.resource_create, name="create"),
    path("type/", views.resource_type_list, name="type-list"),
    path("type/new/", views.resource_type_create, name="type-create"),
    path("type/<slug:slug>/edit/", views.resource_type_update, name="type-update"),
    path("type/<slug:slug>/delete/", views.resource_type_delete, name="type-delete"),
    path("type/<slug:type_slug>/", views.ResourceByTypeListView.as_view(), name="by-type"),
    path("<slug:slug>/", views.ResourceDetailView.as_view(), name="detail"),
    path("<slug:slug>/edit/", views.resource_update, name="update"),
    path("<slug:slug>/delete/", views.resource_delete, name="delete"),
    path("<slug:slug>/database/tables/", views.database_table_list, name="database-tables"),
    path("<slug:slug>/database/tables/new/", views.database_table_create, name="database-table-create"),
    path("<slug:slug>/database/tables/<int:pk>/", views.database_table_detail, name="database-table-detail"),
    path("<slug:slug>/database/tables/<int:pk>/edit/", views.database_table_update, name="database-table-update"),
    path("<slug:slug>/database/tables/<int:pk>/delete/", views.database_table_delete, name="database-table-delete"),
    path("<slug:slug>/database/tables/<int:table_pk>/fields/new/", views.database_field_create, name="database-field-create"),
    path("<slug:slug>/database/tables/<int:table_pk>/fields/<int:pk>/edit/", views.database_field_update, name="database-field-update"),
    path("<slug:slug>/database/tables/<int:table_pk>/fields/<int:pk>/delete/", views.database_field_delete, name="database-field-delete"),
    path("<slug:slug>/database/relationships/", views.database_relationship_list, name="database-relationships"),
    path("<slug:slug>/database/relationships/new/", views.database_relationship_create, name="database-relationship-create"),
    path("<slug:slug>/database/relationships/<int:pk>/edit/", views.database_relationship_update, name="database-relationship-update"),
    path("<slug:slug>/database/relationships/<int:pk>/delete/", views.database_relationship_delete, name="database-relationship-delete"),
    path("<slug:slug>/database/queries/", views.database_query_list, name="database-queries"),
    path("<slug:slug>/database/queries/new/", views.database_query_create, name="database-query-create"),
    path("<slug:slug>/database/queries/<int:pk>/edit/", views.database_query_update, name="database-query-update"),
    path("<slug:slug>/database/queries/<int:pk>/delete/", views.database_query_delete, name="database-query-delete"),
]
