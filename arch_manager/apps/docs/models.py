from django.db import models

from arch_manager.apps.resources.models import Resource


class ResourceDocumentation(models.Model):
    """
    Documentação textual em Markdown de um recurso.
    Integrada ao ecossistema Wagtail para gerenciamento de conteúdo.
    Cada recurso possui no máximo uma documentação principal.
    """

    resource = models.OneToOneField(
        Resource,
        on_delete=models.CASCADE,
        related_name="documentation",
    )
    title = models.CharField(max_length=300)
    markdown_content = models.TextField(blank=True)
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Documentação do Recurso"
        verbose_name_plural = "Documentações de Recursos"

    def __str__(self):
        return f"Documentação: {self.resource.name}"
