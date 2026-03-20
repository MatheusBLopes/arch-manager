from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from .forms import ProjectDocumentationForm, ProjectForm
from .models import Project, ProjectDocumentation


class ProjectListView(ListView):
    model = Project
    context_object_name = "projects"
    template_name = "projects/project_list.html"
    paginate_by = 20

    def get_queryset(self):
        return Project.objects.annotate(resource_count=Count("resources")).order_by("name")


class ProjectDetailView(DetailView):
    model = Project
    context_object_name = "project"
    template_name = "projects/project_detail.html"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Project.objects.prefetch_related("resources__resource_type")


def project_create(request):
    """Criação de novo projeto."""
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            messages.success(request, "Projeto criado com sucesso.")
            return redirect("projects:detail", slug=project.slug)
    else:
        form = ProjectForm()
    return render(request, "projects/project_form.html", {"form": form})


def project_update(request, slug):
    """Edição de projeto existente."""
    project = get_object_or_404(Project, slug=slug)
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Projeto atualizado com sucesso.")
            return redirect("projects:detail", slug=project.slug)
    else:
        form = ProjectForm(instance=project)
    return render(
        request,
        "projects/project_form.html",
        {"form": form, "project": project},
    )


def project_delete(request, slug):
    """Exclusão de projeto."""
    project = get_object_or_404(Project, slug=slug)
    if request.method == "POST":
        project.delete()
        messages.success(request, "Projeto excluído com sucesso.")
        return redirect("projects:list")
    return render(
        request,
        "projects/project_confirm_delete.html",
        {"project": project},
    )


def documentation_edit(request, slug):
    """Criar ou editar documentação Markdown do projeto."""
    project = get_object_or_404(Project, slug=slug)
    doc = getattr(project, "documentation", None)

    if request.method == "POST":
        form = ProjectDocumentationForm(request.POST, instance=doc)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.project = project
            doc.save()
            messages.success(request, "Documentação do projeto salva com sucesso.")
            return redirect("projects:detail", slug=project.slug)
    else:
        if doc:
            form = ProjectDocumentationForm(instance=doc)
        else:
            form = ProjectDocumentationForm(
                initial={"title": f"Documentação: {project.name}"}
            )

    return render(
        request,
        "projects/documentation_form.html",
        {"form": form, "project": project},
    )
