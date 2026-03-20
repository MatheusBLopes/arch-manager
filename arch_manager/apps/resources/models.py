from django.db import models


class ResourceType(models.Model):
    """Tipo do recurso arquitetural (Lambda, SQS, SNS, etc.)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Tipo de Recurso"
        verbose_name_plural = "Tipos de Recurso"

    def __str__(self):
        return self.name


class Resource(models.Model):
    """Recurso arquitetural individual (Lambda, fila SQS, API, etc.)."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    resource_type = models.ForeignKey(
        ResourceType,
        on_delete=models.PROTECT,
        related_name="resources",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resources",
    )
    short_description = models.CharField(max_length=500)
    detailed_description = models.TextField(blank=True)
    runtime_version = models.CharField(
        "Versão do runtime",
        max_length=100,
        blank=True,
        help_text="Ex: python3.12.0, nodejs20.x",
    )
    repository_url = models.URLField("URL do repositório", blank=True)
    has_pentest = models.BooleanField("Possui pentest", default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Recurso"
        verbose_name_plural = "Recursos"

    def __str__(self):
        return f"{self.name} ({self.resource_type.name})"

    def is_database(self):
        """Verifica se o recurso é um banco de dados (RDS, DynamoDB, etc.)."""
        return self.resource_type.slug in ("rds-database", "dynamodb-table")

    def is_api_gateway(self):
        """Verifica se o recurso é um API Gateway."""
        return self.resource_type.slug == "api-gateway"


class DatabaseTable(models.Model):
    """Tabela de um banco de dados (recurso do tipo database)."""

    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="database_tables",
    )
    name = models.CharField("Nome da tabela", max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]
        unique_together = ["resource", "name"]
        verbose_name = "Tabela do Banco"
        verbose_name_plural = "Tabelas do Banco"

    def __str__(self):
        return f"{self.name} ({self.resource.name})"


class TableField(models.Model):
    """Campo/coluna de uma tabela de banco de dados."""

    table = models.ForeignKey(
        DatabaseTable,
        on_delete=models.CASCADE,
        related_name="fields",
    )
    name = models.CharField("Nome do campo", max_length=200)
    data_type = models.CharField("Tipo de dados", max_length=100, blank=True)
    is_primary_key = models.BooleanField("Chave primária", default=False)
    is_nullable = models.BooleanField("Permite nulo", default=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]
        unique_together = ["table", "name"]
        verbose_name = "Campo da Tabela"
        verbose_name_plural = "Campos da Tabela"

    def __str__(self):
        return f"{self.table.name}.{self.name}"


RELATIONSHIP_TYPE_CHOICES = [
    ("one_to_one", "Um para um"),
    ("one_to_many", "Um para muitos"),
    ("many_to_one", "Muitos para um"),
    ("many_to_many", "Muitos para muitos"),
]


class TableRelationship(models.Model):
    """Relacionamento entre duas tabelas do mesmo banco."""

    source_table = models.ForeignKey(
        DatabaseTable,
        on_delete=models.CASCADE,
        related_name="outgoing_relations",
    )
    target_table = models.ForeignKey(
        DatabaseTable,
        on_delete=models.CASCADE,
        related_name="incoming_relations",
    )
    relationship_type = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_TYPE_CHOICES,
        default="one_to_many",
    )
    source_field = models.ForeignKey(
        TableField,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fk_as_source",
    )
    target_field = models.ForeignKey(
        TableField,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fk_as_target",
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["source_table", "target_table"]
        verbose_name = "Relacionamento entre Tabelas"
        verbose_name_plural = "Relacionamentos entre Tabelas"

    def __str__(self):
        return f"{self.source_table.name} --[{self.get_relationship_type_display}]--> {self.target_table.name}"


class DatabaseQuery(models.Model):
    """Query útil cadastrada para um banco de dados."""

    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="database_queries",
    )
    name = models.CharField("Nome", max_length=200)
    description = models.TextField("Descrição explicativa")
    query_text = models.TextField("Query")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Query do Banco"
        verbose_name_plural = "Queries do Banco"

    def __str__(self):
        return f"{self.name} ({self.resource.name})"


# --- API Gateway (recurso tipo api-gateway) ---

HTTP_METHOD_CHOICES = [
    ("GET", "GET"),
    ("POST", "POST"),
    ("PUT", "PUT"),
    ("PATCH", "PATCH"),
    ("DELETE", "DELETE"),
    ("HEAD", "HEAD"),
    ("OPTIONS", "OPTIONS"),
]

PARAM_IN_CHOICES = [
    ("path", "Path"),
    ("query", "Query"),
    ("header", "Header"),
]

PAYLOAD_DIRECTION_CHOICES = [
    ("request", "Request"),
    ("response", "Response"),
]


class ApiGatewayEndpoint(models.Model):
    """Endpoint de um API Gateway (ex: /users, /orders)."""

    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="api_endpoints",
    )
    path = models.CharField("Caminho", max_length=500)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "path"]
        unique_together = ["resource", "path"]
        verbose_name = "Endpoint API"
        verbose_name_plural = "Endpoints API"

    def __str__(self):
        return f"{self.path} ({self.resource.name})"


class ApiGatewayEndpointMethod(models.Model):
    """Método HTTP de um endpoint (GET, POST, etc)."""

    endpoint = models.ForeignKey(
        ApiGatewayEndpoint,
        on_delete=models.CASCADE,
        related_name="methods",
    )
    http_method = models.CharField(
        "Método HTTP",
        max_length=10,
        choices=HTTP_METHOD_CHOICES,
    )
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "http_method"]
        unique_together = ["endpoint", "http_method"]
        verbose_name = "Método do Endpoint"
        verbose_name_plural = "Métodos do Endpoint"

    def __str__(self):
        return f"{self.http_method} {self.endpoint.path}"


class ApiGatewayParameter(models.Model):
    """Parâmetro de um método (path, query, header)."""

    method = models.ForeignKey(
        ApiGatewayEndpointMethod,
        on_delete=models.CASCADE,
        related_name="parameters",
    )
    name = models.CharField("Nome", max_length=200)
    param_in = models.CharField(
        "Local",
        max_length=10,
        choices=PARAM_IN_CHOICES,
    )
    param_type = models.CharField("Tipo", max_length=50, blank=True)
    required = models.BooleanField("Obrigatório", default=False)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]
        unique_together = ["method", "name", "param_in"]
        verbose_name = "Parâmetro API"
        verbose_name_plural = "Parâmetros API"

    def __str__(self):
        return f"{self.name} ({self.get_param_in_display()})"


class ApiGatewayPayload(models.Model):
    """Payload (body) de request ou response de um método."""

    method = models.ForeignKey(
        ApiGatewayEndpointMethod,
        on_delete=models.CASCADE,
        related_name="payloads",
    )
    direction = models.CharField(
        "Direção",
        max_length=10,
        choices=PAYLOAD_DIRECTION_CHOICES,
    )
    content_type = models.CharField(
        "Content-Type",
        max_length=100,
        default="application/json",
    )
    body = models.TextField("Exemplo/Schema", blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "direction"]
        verbose_name = "Payload API"
        verbose_name_plural = "Payloads API"

    def __str__(self):
        return f"{self.get_direction_display()} ({self.method})"


class ApiGatewayInvocation(models.Model):
    """Recurso invocado por um método (Lambda, SQS, etc)."""

    method = models.ForeignKey(
        ApiGatewayEndpointMethod,
        on_delete=models.CASCADE,
        related_name="invocations",
    )
    target_resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="invoked_by_api_methods",
    )
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "Invocação API"
        verbose_name_plural = "Invocações API"

    def __str__(self):
        return f"{self.method} -> {self.target_resource.name}"


class ApiGatewayExampleCurl(models.Model):
    """Exemplo de curl para um método."""

    method = models.ForeignKey(
        ApiGatewayEndpointMethod,
        on_delete=models.CASCADE,
        related_name="example_curls",
    )
    label = models.CharField("Rótulo", max_length=200)
    curl_command = models.TextField("Comando curl")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "label"]
        verbose_name = "Exemplo curl"
        verbose_name_plural = "Exemplos curl"

    def __str__(self):
        return f"{self.label} ({self.method})"
