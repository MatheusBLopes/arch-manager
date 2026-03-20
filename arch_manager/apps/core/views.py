from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render

from arch_manager.apps.resources.models import Resource, ResourceType

from .pdf_export import build_pdf_buffer


def dashboard(request):
    """Dashboard inicial com resumo de recursos e atalhos."""
    resource_types = ResourceType.objects.filter(is_active=True).annotate(
        count=Count("resources")
    )
    total_resources = Resource.objects.count()
    recent_resources = Resource.objects.order_by("-created_at")[:10]

    context = {
        "resource_types": resource_types,
        "total_resources": total_resources,
        "recent_resources": recent_resources,
    }
    return render(request, "core/dashboard.html", context)


def pdf_export(request):
    """Gera PDF com toda a documentação do sistema."""
    pdf_bytes = build_pdf_buffer()
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="arch-manager-documentacao.pdf"'
    return response
