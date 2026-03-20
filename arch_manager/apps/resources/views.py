from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from .forms import (
    ApiGatewayEndpointForm,
    ApiGatewayEndpointMethodForm,
    ApiGatewayExampleCurlForm,
    ApiGatewayInvocationForm,
    ApiGatewayParameterForm,
    ApiGatewayPayloadForm,
    DatabaseQueryForm,
    DatabaseTableForm,
    LambdaDetailsForm,
    ResourceForm,
    ResourceTypeForm,
    TableFieldForm,
    TableRelationshipForm,
)
from .models import (
    ApiGatewayEndpoint,
    ApiGatewayEndpointMethod,
    ApiGatewayExampleCurl,
    ApiGatewayInvocation,
    ApiGatewayParameter,
    ApiGatewayPayload,
    DatabaseQuery,
    DatabaseTable,
    LambdaDetails,
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
        qs = Resource.objects.all().select_related("resource_type", "lambda_details")
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
        ).select_related("resource_type", "lambda_details").order_by("name")

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
        return Resource.objects.select_related(
            "resource_type", "project", "lambda_details"
        ).prefetch_related(
            "outgoing_relationships__target_resource",
            "incoming_relationships__source_resource",
        )


def resource_create(request):
    """Criação de novo recurso (FBV para redirect correto)."""
    initial = {}
    if type_slug := request.GET.get("type"):
        rt = ResourceType.objects.filter(slug=type_slug, is_active=True).first()
        if rt:
            initial["resource_type"] = rt

    if request.method == "POST":
        form = ResourceForm(request.POST)
        lambda_form = LambdaDetailsForm(request.POST)
        if form.is_valid():
            resource = form.save()
            if resource.is_lambda() and lambda_form.is_valid():
                lambda_form.instance.resource = resource
                lambda_form.save()
            messages.success(request, "Recurso criado com sucesso.")
            return redirect("resources:detail", slug=resource.slug)
    else:
        form = ResourceForm(initial=initial)
        lambda_form = LambdaDetailsForm()
    lambda_type = ResourceType.objects.filter(slug="lambda", is_active=True).first()
    return render(
        request,
        "resources/resource_form.html",
        {
            "form": form,
            "lambda_form": lambda_form,
            "resource": None,
            "lambda_type_pk": lambda_type.pk if lambda_type else None,
        },
    )


def resource_update(request, slug):
    """Edição de recurso existente."""
    resource = get_object_or_404(Resource, slug=slug)
    lambda_details = getattr(resource, "lambda_details", None)

    if request.method == "POST":
        form = ResourceForm(request.POST, instance=resource)
        lambda_form = LambdaDetailsForm(
            request.POST,
            instance=lambda_details,
        )
        if form.is_valid():
            form.save()
            if resource.is_lambda() and lambda_form.is_valid():
                lambda_form.instance.resource = resource
                lambda_form.save()
            messages.success(request, "Recurso atualizado com sucesso.")
            return redirect("resources:detail", slug=resource.slug)
    else:
        form = ResourceForm(instance=resource)
        lambda_form = LambdaDetailsForm(instance=lambda_details) if lambda_details else LambdaDetailsForm()

    lambda_type = ResourceType.objects.filter(slug="lambda", is_active=True).first()
    return render(
        request,
        "resources/resource_form.html",
        {
            "form": form,
            "lambda_form": lambda_form,
            "resource": resource,
            "lambda_type_pk": lambda_type.pk if lambda_type else None,
        },
    )


def resource_delete(request, slug):
    """Exclusão de recurso."""
    resource = get_object_or_404(Resource, slug=slug)
    if request.method == "POST":
        resource.delete()
        messages.success(request, "Recurso excluído com sucesso.")
        return redirect("resources:list")
    messages.error(request, "Método inválido.")
    return redirect("resources:detail", slug=slug)


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


def resource_type_delete(request, slug):
    """Exclusão de tipo de recurso (apenas se não houver recursos vinculados)."""
    resource_type = get_object_or_404(ResourceType, slug=slug)
    if request.method == "POST":
        if resource_type.resources.exists():
            messages.error(
                request,
                f"Não é possível excluir o tipo \"{resource_type.name}\": existem recursos vinculados.",
            )
            return redirect("resources:type-list")
        resource_type.delete()
        messages.success(request, "Tipo de recurso excluído com sucesso.")
        return redirect("resources:type-list")
    messages.error(request, "Método inválido.")
    return redirect("resources:type-list")


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
    return redirect("resources:database-tables", slug=slug)


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
    return redirect("resources:database-table-detail", slug=slug, pk=table_pk)


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
    return redirect("resources:database-relationships", slug=slug)


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
    return redirect("resources:database-queries", slug=slug)


# --- API Gateway ---


def _get_api_gateway_resource(request, slug):
    """Obtém recurso e verifica se é API Gateway."""
    resource = get_object_or_404(Resource, slug=slug)
    if not resource.is_api_gateway():
        messages.error(request, "Este recurso não é um API Gateway.")
        return None, redirect("resources:detail", slug=slug)
    return resource, None


def api_endpoint_list(request, slug):
    """Lista endpoints do API Gateway."""
    resource, err = _get_api_gateway_resource(request, slug)
    if err:
        return err
    endpoints = ApiGatewayEndpoint.objects.filter(resource=resource).prefetch_related("methods")
    return render(request, "resources/api/endpoint_list.html", {"resource": resource, "endpoints": endpoints})


def api_endpoint_create(request, slug):
    """Cria endpoint."""
    resource, err = _get_api_gateway_resource(request, slug)
    if err:
        return err
    if request.method == "POST":
        form = ApiGatewayEndpointForm(request.POST)
        if form.is_valid():
            endpoint = form.save(commit=False)
            endpoint.resource = resource
            endpoint.save()
            messages.success(request, "Endpoint criado.")
            return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint.pk)
    else:
        form = ApiGatewayEndpointForm()
    return render(request, "resources/api/endpoint_form.html", {"form": form, "resource": resource})


def api_endpoint_detail(request, slug, pk):
    """Detalhe do endpoint com métodos e subitens."""
    resource, err = _get_api_gateway_resource(request, slug)
    if err:
        return err
    endpoint = get_object_or_404(ApiGatewayEndpoint, pk=pk, resource=resource)
    methods = endpoint.methods.prefetch_related(
        "parameters",
        "payloads",
        "invocations__target_resource",
        "example_curls",
    ).order_by("order", "http_method")
    return render(
        request,
        "resources/api/endpoint_detail.html",
        {"resource": resource, "endpoint": endpoint, "methods": methods},
    )


def api_endpoint_update(request, slug, pk):
    """Edita endpoint."""
    resource, err = _get_api_gateway_resource(request, slug)
    if err:
        return err
    endpoint = get_object_or_404(ApiGatewayEndpoint, pk=pk, resource=resource)
    if request.method == "POST":
        form = ApiGatewayEndpointForm(request.POST, instance=endpoint)
        if form.is_valid():
            form.save()
            messages.success(request, "Endpoint atualizado.")
            return redirect("resources:api-endpoint-detail", slug=slug, pk=pk)
    else:
        form = ApiGatewayEndpointForm(instance=endpoint)
    return render(
        request,
        "resources/api/endpoint_form.html",
        {"form": form, "resource": resource, "endpoint": endpoint},
    )


def api_endpoint_delete(request, slug, pk):
    """Remove endpoint."""
    resource, err = _get_api_gateway_resource(request, slug)
    if err:
        return err
    endpoint = get_object_or_404(ApiGatewayEndpoint, pk=pk, resource=resource)
    if request.method == "POST":
        endpoint.delete()
        messages.success(request, "Endpoint removido.")
        return redirect("resources:api-endpoint-list", slug=slug)
    return redirect("resources:api-endpoint-list", slug=slug)


def api_method_create(request, slug, endpoint_pk):
    """Cria método em um endpoint."""
    resource, err = _get_api_gateway_resource(request, slug)
    if err:
        return err
    endpoint = get_object_or_404(ApiGatewayEndpoint, pk=endpoint_pk, resource=resource)
    if request.method == "POST":
        form = ApiGatewayEndpointMethodForm(request.POST)
        if form.is_valid():
            method = form.save(commit=False)
            method.endpoint = endpoint
            method.save()
            messages.success(request, "Método criado.")
            return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)
    else:
        form = ApiGatewayEndpointMethodForm()
    return render(
        request,
        "resources/api/method_form.html",
        {"form": form, "resource": resource, "endpoint": endpoint},
    )


def api_method_update(request, slug, endpoint_pk, pk):
    """Edita método."""
    resource, err = _get_api_gateway_resource(request, slug)
    if err:
        return err
    endpoint = get_object_or_404(ApiGatewayEndpoint, pk=endpoint_pk, resource=resource)
    method = get_object_or_404(ApiGatewayEndpointMethod, pk=pk, endpoint=endpoint)
    if request.method == "POST":
        form = ApiGatewayEndpointMethodForm(request.POST, instance=method)
        if form.is_valid():
            form.save()
            messages.success(request, "Método atualizado.")
            return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)
    else:
        form = ApiGatewayEndpointMethodForm(instance=method)
    return render(
        request,
        "resources/api/method_form.html",
        {"form": form, "resource": resource, "endpoint": endpoint, "method": method},
    )


def api_method_delete(request, slug, endpoint_pk, pk):
    """Remove método."""
    resource, err = _get_api_gateway_resource(request, slug)
    if err:
        return err
    endpoint = get_object_or_404(ApiGatewayEndpoint, pk=endpoint_pk, resource=resource)
    method = get_object_or_404(ApiGatewayEndpointMethod, pk=pk, endpoint=endpoint)
    if request.method == "POST":
        method.delete()
        messages.success(request, "Método removido.")
        return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)
    return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)


def api_parameter_create(request, slug, endpoint_pk, method_pk):
    """Cria parâmetro em um método."""
    resource, err = _get_api_gateway_resource(request, slug)
    if err:
        return err
    endpoint = get_object_or_404(ApiGatewayEndpoint, pk=endpoint_pk, resource=resource)
    method = get_object_or_404(ApiGatewayEndpointMethod, pk=method_pk, endpoint=endpoint)
    if request.method == "POST":
        form = ApiGatewayParameterForm(request.POST)
        if form.is_valid():
            param = form.save(commit=False)
            param.method = method
            param.save()
            messages.success(request, "Parâmetro criado.")
            return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)
    else:
        form = ApiGatewayParameterForm()
    return render(
        request,
        "resources/api/parameter_form.html",
        {"form": form, "resource": resource, "endpoint": endpoint, "method": method},
    )


def api_parameter_update(request, slug, endpoint_pk, method_pk, pk):
    """Edita parâmetro."""
    resource, err = _get_api_gateway_resource(request, slug)
    if err:
        return err
    endpoint = get_object_or_404(ApiGatewayEndpoint, pk=endpoint_pk, resource=resource)
    method = get_object_or_404(ApiGatewayEndpointMethod, pk=method_pk, endpoint=endpoint)
    param = get_object_or_404(ApiGatewayParameter, pk=pk, method=method)
    if request.method == "POST":
        form = ApiGatewayParameterForm(request.POST, instance=param)
        if form.is_valid():
            form.save()
            messages.success(request, "Parâmetro atualizado.")
            return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)
    else:
        form = ApiGatewayParameterForm(instance=param)
    return render(
        request,
        "resources/api/parameter_form.html",
        {"form": form, "resource": resource, "endpoint": endpoint, "method": method, "parameter": param},
    )


def api_parameter_delete(request, slug, endpoint_pk, method_pk, pk):
    """Remove parâmetro."""
    resource, err = _get_api_gateway_resource(request, slug)
    if err:
        return err
    param = get_object_or_404(ApiGatewayParameter, pk=pk, method__endpoint__resource__slug=slug)
    if request.method == "POST":
        param.delete()
        messages.success(request, "Parâmetro removido.")
        return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)
    return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)


def api_payload_create(request, slug, endpoint_pk, method_pk):
    """Cria payload em um método."""
    resource, err = _get_api_gateway_resource(request, slug)
    if err:
        return err
    endpoint = get_object_or_404(ApiGatewayEndpoint, pk=endpoint_pk, resource=resource)
    method = get_object_or_404(ApiGatewayEndpointMethod, pk=method_pk, endpoint=endpoint)
    if request.method == "POST":
        form = ApiGatewayPayloadForm(request.POST)
        if form.is_valid():
            payload = form.save(commit=False)
            payload.method = method
            payload.save()
            messages.success(request, "Payload criado.")
            return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)
    else:
        form = ApiGatewayPayloadForm()
    return render(
        request,
        "resources/api/payload_form.html",
        {"form": form, "resource": resource, "endpoint": endpoint, "method": method},
    )


def api_payload_update(request, slug, endpoint_pk, method_pk, pk):
    """Edita payload."""
    resource, err = _get_api_gateway_resource(request, slug)
    if err:
        return err
    endpoint = get_object_or_404(ApiGatewayEndpoint, pk=endpoint_pk, resource=resource)
    method = get_object_or_404(ApiGatewayEndpointMethod, pk=method_pk, endpoint=endpoint)
    payload = get_object_or_404(ApiGatewayPayload, pk=pk, method=method)
    if request.method == "POST":
        form = ApiGatewayPayloadForm(request.POST, instance=payload)
        if form.is_valid():
            form.save()
            messages.success(request, "Payload atualizado.")
            return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)
    else:
        form = ApiGatewayPayloadForm(instance=payload)
    return render(
        request,
        "resources/api/payload_form.html",
        {"form": form, "resource": resource, "endpoint": endpoint, "method": method, "payload": payload},
    )


def api_payload_delete(request, slug, endpoint_pk, method_pk, pk):
    """Remove payload."""
    payload = get_object_or_404(ApiGatewayPayload, pk=pk, method__endpoint__resource__slug=slug)
    if request.method == "POST":
        payload.delete()
        messages.success(request, "Payload removido.")
        return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)
    return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)


def api_invocation_create(request, slug, endpoint_pk, method_pk):
    """Cria invocação em um método."""
    resource, err = _get_api_gateway_resource(request, slug)
    if err:
        return err
    endpoint = get_object_or_404(ApiGatewayEndpoint, pk=endpoint_pk, resource=resource)
    method = get_object_or_404(ApiGatewayEndpointMethod, pk=method_pk, endpoint=endpoint)
    if request.method == "POST":
        form = ApiGatewayInvocationForm(request.POST, resource=resource)
        if form.is_valid():
            inv = form.save(commit=False)
            inv.method = method
            inv.save()
            messages.success(request, "Invocação cadastrada.")
            return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)
    else:
        form = ApiGatewayInvocationForm(resource=resource)
    return render(
        request,
        "resources/api/invocation_form.html",
        {"form": form, "resource": resource, "endpoint": endpoint, "method": method},
    )


def api_invocation_update(request, slug, endpoint_pk, method_pk, pk):
    """Edita invocação."""
    resource, err = _get_api_gateway_resource(request, slug)
    if err:
        return err
    endpoint = get_object_or_404(ApiGatewayEndpoint, pk=endpoint_pk, resource=resource)
    method = get_object_or_404(ApiGatewayEndpointMethod, pk=method_pk, endpoint=endpoint)
    inv = get_object_or_404(ApiGatewayInvocation, pk=pk, method=method)
    if request.method == "POST":
        form = ApiGatewayInvocationForm(request.POST, instance=inv, resource=resource)
        if form.is_valid():
            form.save()
            messages.success(request, "Invocação atualizada.")
            return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)
    else:
        form = ApiGatewayInvocationForm(instance=inv, resource=resource)
    return render(
        request,
        "resources/api/invocation_form.html",
        {"form": form, "resource": resource, "endpoint": endpoint, "method": method, "invocation": inv},
    )


def api_invocation_delete(request, slug, endpoint_pk, method_pk, pk):
    """Remove invocação."""
    inv = get_object_or_404(ApiGatewayInvocation, pk=pk, method__endpoint__resource__slug=slug)
    if request.method == "POST":
        inv.delete()
        messages.success(request, "Invocação removida.")
        return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)
    return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)


def api_example_curl_create(request, slug, endpoint_pk, method_pk):
    """Cria exemplo curl em um método."""
    resource, err = _get_api_gateway_resource(request, slug)
    if err:
        return err
    endpoint = get_object_or_404(ApiGatewayEndpoint, pk=endpoint_pk, resource=resource)
    method = get_object_or_404(ApiGatewayEndpointMethod, pk=method_pk, endpoint=endpoint)
    if request.method == "POST":
        form = ApiGatewayExampleCurlForm(request.POST)
        if form.is_valid():
            curl = form.save(commit=False)
            curl.method = method
            curl.save()
            messages.success(request, "Exemplo curl criado.")
            return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)
    else:
        form = ApiGatewayExampleCurlForm()
    return render(
        request,
        "resources/api/example_curl_form.html",
        {"form": form, "resource": resource, "endpoint": endpoint, "method": method},
    )


def api_example_curl_update(request, slug, endpoint_pk, method_pk, pk):
    """Edita exemplo curl."""
    resource, err = _get_api_gateway_resource(request, slug)
    if err:
        return err
    endpoint = get_object_or_404(ApiGatewayEndpoint, pk=endpoint_pk, resource=resource)
    method = get_object_or_404(ApiGatewayEndpointMethod, pk=method_pk, endpoint=endpoint)
    curl = get_object_or_404(ApiGatewayExampleCurl, pk=pk, method=method)
    if request.method == "POST":
        form = ApiGatewayExampleCurlForm(request.POST, instance=curl)
        if form.is_valid():
            form.save()
            messages.success(request, "Exemplo curl atualizado.")
            return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)
    else:
        form = ApiGatewayExampleCurlForm(instance=curl)
    return render(
        request,
        "resources/api/example_curl_form.html",
        {"form": form, "resource": resource, "endpoint": endpoint, "method": method, "example_curl": curl},
    )


def api_example_curl_delete(request, slug, endpoint_pk, method_pk, pk):
    """Remove exemplo curl."""
    curl = get_object_or_404(ApiGatewayExampleCurl, pk=pk, method__endpoint__resource__slug=slug)
    if request.method == "POST":
        curl.delete()
        messages.success(request, "Exemplo curl removido.")
        return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)
    return redirect("resources:api-endpoint-detail", slug=slug, pk=endpoint_pk)
