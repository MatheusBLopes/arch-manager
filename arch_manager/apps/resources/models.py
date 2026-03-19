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
    short_description = models.CharField(max_length=500)
    detailed_description = models.TextField(blank=True)
    runtime_version = models.CharField(
        "Versão do runtime",
        max_length=100,
        blank=True,
        help_text="Ex: python3.12.0, nodejs20.x",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Recurso"
        verbose_name_plural = "Recursos"

    def __str__(self):
        return f"{self.name} ({self.resource_type.name})"
