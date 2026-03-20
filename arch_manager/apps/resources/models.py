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
