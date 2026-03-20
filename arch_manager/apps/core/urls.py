from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("export/pdf/", views.pdf_export, name="pdf-export"),
]
