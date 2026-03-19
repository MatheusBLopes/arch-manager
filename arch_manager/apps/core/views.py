from django.db.models import Count, Q
from django.shortcuts import render

from arch_manager.apps.resources.models import Resource, ResourceType


def dashboard(request):
    """Dashboard inicial com resumo de recursos e atalhos."""
    resource_types = ResourceType.objects.filter(is_active=True).annotate(
        count=Count("resources", filter=Q(resources__is_active=True))
    )
    total_resources = Resource.objects.filter(is_active=True).count()
    recent_resources = Resource.objects.filter(is_active=True).order_by("-created_at")[:10]

    context = {
        "resource_types": resource_types,
        "total_resources": total_resources,
        "recent_resources": recent_resources,
    }
    return render(request, "core/dashboard.html", context)
