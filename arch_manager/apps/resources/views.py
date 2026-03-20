from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from .forms import (
    DatabaseQueryForm,
    DatabaseTableForm,
    ResourceForm,
    ResourceTypeForm,
    TableFieldForm,
    TableRelationshipForm,
)
from .models import (
    DatabaseQuery,
    DatabaseTable,
    Resource,
    ResourceType,
    TableField,
    TableRelationship,
)


class ResourceListView(ListView):
    """Listagem geral de recursos com busca e filtro por tipo."""
    model = Resource
    context_object_name = "resources"
    template_name = "resources/resource_list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = Resource.objects.all().select_related("resource_type")
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
        return Resource.objects.select_related("resource_type", "project").prefetch_related(
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
        resource_count=Count("resources")
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


def _get_database_resource(request, slug):
    """Obtém recurso e verifica se é banco de dados."""
    resource = get_object_or_404(Resource, slug=slug)
    if not resource.is_database():
        messages.error(request, "Este recurso não é um banco de dados.")
        return None, redirect("resources:detail", slug=slug)
    return resource, None


def database_table_list(request, slug):
    """Lista tabelas do banco."""
    resource, err = _get_database_resource(request, slug)
    if err:
        return err
    tables = DatabaseTable.objects.filter(resource=resource).prefetch_related("fields")
    return render(request, "resources/database/table_list.html", {"resource": resource, "tables": tables})


def database_table_create(request, slug):
    """Cria tabela."""
    resource, err = _get_database_resource(request, slug)
    if err:
        return err
    if request.method == "POST":
        form = DatabaseTableForm(request.POST)
        if form.is_valid():
            table = form.save(commit=False)
            table.resource = resource
            table.save()
            messages.success(request, "Tabela criada.")
            return redirect("resources:database-tables", slug=slug)
    else:
        form = DatabaseTableForm()
    return render(request, "resources/database/table_form.html", {"form": form, "resource": resource})


def database_table_update(request, slug, pk):
    """Edita tabela."""
    resource, err = _get_database_resource(request, slug)
    if err:
        return err
    table = get_object_or_404(DatabaseTable, pk=pk, resource=resource)
    if request.method == "POST":
        form = DatabaseTableForm(request.POST, instance=table)
        if form.is_valid():
            form.save()
            messages.success(request, "Tabela atualizada.")
            return redirect("resources:database-tables", slug=slug)
    else:
        form = DatabaseTableForm(instance=table)
    return render(request, "resources/database/table_form.html", {"form": form, "resource": resource, "table": table})


def database_table_delete(request, slug, pk):
    """Remove tabela."""
    resource, err = _get_database_resource(request, slug)
    if err:
        return err
    table = get_object_or_404(DatabaseTable, pk=pk, resource=resource)
    if request.method == "POST":
        table.delete()
        messages.success(request, "Tabela removida.")
        return redirect("resources:database-tables", slug=slug)
    return render(request, "resources/database/table_confirm_delete.html", {"resource": resource, "table": table})


def database_table_detail(request, slug, pk):
    """Detalhe da tabela com campos."""
    resource, err = _get_database_resource(request, slug)
    if err:
        return err
    table = get_object_or_404(DatabaseTable, pk=pk, resource=resource)
    fields = TableField.objects.filter(table=table)
    return render(request, "resources/database/table_detail.html", {"resource": resource, "table": table, "fields": fields})


def database_field_create(request, slug, table_pk):
    """Cria campo em uma tabela."""
    resource, err = _get_database_resource(request, slug)
    if err:
        return err
    table = get_object_or_404(DatabaseTable, pk=table_pk, resource=resource)
    if request.method == "POST":
        form = TableFieldForm(request.POST)
        if form.is_valid():
            field = form.save(commit=False)
            field.table = table
            field.save()
            messages.success(request, "Campo criado.")
            return redirect("resources:database-table-detail", slug=slug, pk=table_pk)
    else:
        form = TableFieldForm()
    return render(request, "resources/database/field_form.html", {"form": form, "resource": resource, "table": table})


def database_field_update(request, slug, table_pk, pk):
    """Edita campo."""
    resource, err = _get_database_resource(request, slug)
    if err:
        return err
    table = get_object_or_404(DatabaseTable, pk=table_pk, resource=resource)
    field = get_object_or_404(TableField, pk=pk, table=table)
    if request.method == "POST":
        form = TableFieldForm(request.POST, instance=field)
        if form.is_valid():
            form.save()
            messages.success(request, "Campo atualizado.")
            return redirect("resources:database-table-detail", slug=slug, pk=table_pk)
    else:
        form = TableFieldForm(instance=field)
    return render(request, "resources/database/field_form.html", {"form": form, "resource": resource, "table": table, "field": field})


def database_field_delete(request, slug, table_pk, pk):
    """Remove campo."""
    resource, err = _get_database_resource(request, slug)
    if err:
        return err
    table = get_object_or_404(DatabaseTable, pk=table_pk, resource=resource)
    field = get_object_or_404(TableField, pk=pk, table=table)
    if request.method == "POST":
        field.delete()
        messages.success(request, "Campo removido.")
        return redirect("resources:database-table-detail", slug=slug, pk=table_pk)
    return render(request, "resources/database/field_confirm_delete.html", {"resource": resource, "table": table, "field": field})


def database_relationship_list(request, slug):
    """Lista relacionamentos entre tabelas."""
    resource, err = _get_database_resource(request, slug)
    if err:
        return err
    relationships = TableRelationship.objects.filter(source_table__resource=resource).select_related("source_table", "target_table")
    return render(request, "resources/database/relationship_list.html", {"resource": resource, "relationships": relationships})


def database_relationship_create(request, slug):
    """Cria relacionamento entre tabelas."""
    resource, err = _get_database_resource(request, slug)
    if err:
        return err
    if request.method == "POST":
        form = TableRelationshipForm(request.POST, resource=resource)
        if form.is_valid():
            form.save()
            messages.success(request, "Relacionamento criado.")
            return redirect("resources:database-relationships", slug=slug)
    else:
        form = TableRelationshipForm(resource=resource)
    return render(request, "resources/database/relationship_form.html", {"form": form, "resource": resource})


def database_relationship_update(request, slug, pk):
    """Edita relacionamento."""
    resource, err = _get_database_resource(request, slug)
    if err:
        return err
    rel = get_object_or_404(TableRelationship, pk=pk, source_table__resource=resource)
    if request.method == "POST":
        form = TableRelationshipForm(request.POST, instance=rel, resource=resource)
        if form.is_valid():
            form.save()
            messages.success(request, "Relacionamento atualizado.")
            return redirect("resources:database-relationships", slug=slug)
    else:
        form = TableRelationshipForm(instance=rel, resource=resource)
    return render(request, "resources/database/relationship_form.html", {"form": form, "resource": resource, "relationship": rel})


def database_relationship_delete(request, slug, pk):
    """Remove relacionamento."""
    resource, err = _get_database_resource(request, slug)
    if err:
        return err
    rel = get_object_or_404(TableRelationship, pk=pk, source_table__resource=resource)
    if request.method == "POST":
        rel.delete()
        messages.success(request, "Relacionamento removido.")
        return redirect("resources:database-relationships", slug=slug)
    return render(request, "resources/database/relationship_confirm_delete.html", {"resource": resource, "relationship": rel})


def database_query_list(request, slug):
    """Lista queries úteis do banco."""
    resource, err = _get_database_resource(request, slug)
    if err:
        return err
    queries = DatabaseQuery.objects.filter(resource=resource)
    return render(request, "resources/database/query_list.html", {"resource": resource, "queries": queries})


def database_query_create(request, slug):
    """Cria query útil."""
    resource, err = _get_database_resource(request, slug)
    if err:
        return err
    if request.method == "POST":
        form = DatabaseQueryForm(request.POST)
        if form.is_valid():
            query = form.save(commit=False)
            query.resource = resource
            query.save()
            messages.success(request, "Query cadastrada.")
            return redirect("resources:database-queries", slug=slug)
    else:
        form = DatabaseQueryForm()
    return render(request, "resources/database/query_form.html", {"form": form, "resource": resource})


def database_query_update(request, slug, pk):
    """Edita query."""
    resource, err = _get_database_resource(request, slug)
    if err:
        return err
    query = get_object_or_404(DatabaseQuery, pk=pk, resource=resource)
    if request.method == "POST":
        form = DatabaseQueryForm(request.POST, instance=query)
        if form.is_valid():
            form.save()
            messages.success(request, "Query atualizada.")
            return redirect("resources:database-queries", slug=slug)
    else:
        form = DatabaseQueryForm(instance=query)
    return render(request, "resources/database/query_form.html", {"form": form, "resource": resource, "query": query})


def database_query_delete(request, slug, pk):
    """Remove query."""
    resource, err = _get_database_resource(request, slug)
    if err:
        return err
    query = get_object_or_404(DatabaseQuery, pk=pk, resource=resource)
    if request.method == "POST":
        query.delete()
        messages.success(request, "Query removida.")
        return redirect("resources:database-queries", slug=slug)
    return render(request, "resources/database/query_confirm_delete.html", {"resource": resource, "query": query})
