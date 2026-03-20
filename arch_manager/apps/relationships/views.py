from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from arch_manager.apps.resources.models import Resource

from .forms import ResourceRelationshipForm
from .models import ResourceRelationship


def relationship_create(request, resource_slug=None):
    """Criação de novo relacionamento."""
    source_resource = None
    if resource_slug:
        source_resource = get_object_or_404(Resource, slug=resource_slug)

    if request.method == "POST":
        form = ResourceRelationshipForm(request.POST)
        if form.is_valid():
            rel = form.save()
            messages.success(request, "Relacionamento criado com sucesso.")
            return redirect("resources:detail", slug=rel.source_resource.slug)
    else:
        initial = {}
        if source_resource:
            initial["source_resource"] = source_resource
        form = ResourceRelationshipForm(initial=initial)

    return render(
        request,
        "relationships/relationship_form.html",
        {"form": form, "source_resource": source_resource},
    )


def relationship_update(request, pk):
    """Edição de relacionamento existente."""
    relationship = get_object_or_404(ResourceRelationship, pk=pk)

    if request.method == "POST":
        form = ResourceRelationshipForm(request.POST, instance=relationship)
        if form.is_valid():
            form.save()
            messages.success(request, "Relacionamento atualizado com sucesso.")
            return redirect("resources:detail", slug=relationship.source_resource.slug)
    else:
        form = ResourceRelationshipForm(instance=relationship)

    return render(
        request,
        "relationships/relationship_form.html",
        {"form": form, "relationship": relationship},
    )


def relationship_delete(request, pk):
    """Remoção de relacionamento."""
    relationship = get_object_or_404(ResourceRelationship, pk=pk)
    if request.method == "POST":
        source_slug = relationship.source_resource.slug
        relationship.delete()
        messages.success(request, "Relacionamento removido.")
        return redirect("resources:detail", slug=source_slug)
    return redirect("resources:detail", slug=relationship.source_resource.slug)
