from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from .forms import ResourceForm, ResourceTypeForm
from .models import Resource, ResourceType


class ResourceListView(ListView):
    """Listagem geral de recursos com busca e filtro por tipo."""
    model = Resource
    context_object_name = "resources"
    template_name = "resources/resource_list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = Resource.objects.filter(is_active=True).select_related("resource_type")
        search = self.request.GET.get("q", "").strip()
        type_slug = self.request.GET.get("type", "").strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(short_description__icontains=search)
                | Q(resource_type__name__icontains=search)
            )
        if type_slug:
            qs = qs.filter(resource_type__slug=type_slug)
        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["resource_types"] = ResourceType.objects.filter(is_active=True)
        context["search"] = self.request.GET.get("q", "")
        context["type_filter"] = self.request.GET.get("type", "")
        return context


class ResourceByTypeListView(ListView):
    """Listagem de recursos por tipo."""
    model = Resource
    context_object_name = "resources"
    template_name = "resources/resource_by_type.html"
    paginate_by = 20

    def get_queryset(self):
        self.resource_type = get_object_or_404(
            ResourceType,
            slug=self.kwargs["type_slug"],
            is_active=True,
        )
        return Resource.objects.filter(
            resource_type=self.resource_type,
            is_active=True,
        ).select_related("resource_type").order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["resource_type"] = self.resource_type
        return context


class ResourceDetailView(DetailView):
    """Detalhes completos do recurso com documentação e relacionamentos."""
    model = Resource
    context_object_name = "resource"
    template_name = "resources/resource_detail.html"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Resource.objects.select_related("resource_type").prefetch_related(
            "outgoing_relationships__target_resource",
            "incoming_relationships__source_resource",
        )


def resource_create(request):
    """Criação de novo recurso (FBV para redirect correto)."""
    if request.method == "POST":
        form = ResourceForm(request.POST)
        if form.is_valid():
            resource = form.save()
            messages.success(request, "Recurso criado com sucesso.")
            return redirect("resources:detail", slug=resource.slug)
    else:
        initial = {}
        if type_slug := request.GET.get("type"):
            rt = ResourceType.objects.filter(slug=type_slug, is_active=True).first()
            if rt:
                initial["resource_type"] = rt
        form = ResourceForm(initial=initial)
    return render(request, "resources/resource_form.html", {"form": form})


def resource_update(request, slug):
    """Edição de recurso existente."""
    resource = get_object_or_404(Resource, slug=slug)
    if request.method == "POST":
        form = ResourceForm(request.POST, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, "Recurso atualizado com sucesso.")
            return redirect("resources:detail", slug=resource.slug)
    else:
        form = ResourceForm(instance=resource)
    return render(request, "resources/resource_form.html", {"form": form, "resource": resource})


def resource_type_list(request):
    """Listagem de tipos de recurso."""
    types = ResourceType.objects.filter(is_active=True).annotate(
        resource_count=Count("resources", filter=Q(resources__is_active=True))
    )
    return render(
        request,
        "resources/resource_type_list.html",
        {"resource_types": types},
    )


def resource_type_create(request):
    """Criação de tipo de recurso."""
    if request.method == "POST":
        form = ResourceTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo de recurso criado com sucesso.")
            return redirect("resources:type-list")
    else:
        form = ResourceTypeForm()
    return render(request, "resources/resource_type_form.html", {"form": form})


def resource_type_update(request, slug):
    """Edição de tipo de recurso."""
    resource_type = get_object_or_404(ResourceType, slug=slug)
    if request.method == "POST":
        form = ResourceTypeForm(request.POST, instance=resource_type)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo de recurso atualizado com sucesso.")
            return redirect("resources:type-list")
    else:
        form = ResourceTypeForm(instance=resource_type)
    return render(
        request,
        "resources/resource_type_form.html",
        {"form": form, "resource_type": resource_type},
    )
