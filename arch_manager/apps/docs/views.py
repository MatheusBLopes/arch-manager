import markdown
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from arch_manager.apps.resources.models import Resource

from .forms import ResourceDocumentationForm
from .models import ResourceDocumentation


def documentation_edit(request, resource_slug):
    """Criar ou editar documentação Markdown do recurso."""
    resource = get_object_or_404(Resource, slug=resource_slug)
    doc = getattr(resource, "documentation", None)

    if request.method == "POST":
        form = ResourceDocumentationForm(request.POST, instance=doc)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.resource = resource
            doc.save()
            messages.success(request, "Documentação salva com sucesso.")
            return redirect("resources:detail", slug=resource.slug)
    else:
        if doc:
            form = ResourceDocumentationForm(instance=doc)
        else:
            form = ResourceDocumentationForm(
                initial={"title": f"Documentação: {resource.name}"}
            )

    return render(
        request,
        "docs/documentation_form.html",
        {"form": form, "resource": resource},
    )


def render_markdown(text):
    """Renderiza conteúdo Markdown para HTML de forma segura."""
    if not text:
        return ""
    return markdown.markdown(
        text,
        extensions=["extra", "codehilite", "toc"],
        extension_configs={
            "codehilite": {"css_class": "highlight"},
        },
    )
