from django.db import models


class Project(models.Model):
    """Projeto que agrupa recursos com documentação mais ampla."""

    name = models.CharField("Nome", max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    short_description = models.CharField("Descrição curta", max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"

    def __str__(self):
        return self.name


class ProjectDocumentation(models.Model):
    """Documentação genérica do projeto em Markdown."""

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="documentation",
    )
    title = models.CharField("Título", max_length=300)
    markdown_content = models.TextField("Conteúdo Markdown", blank=True)
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Documentação do Projeto"
        verbose_name_plural = "Documentações de Projetos"

    def __str__(self):
        return f"Documentação: {self.project.name}"
