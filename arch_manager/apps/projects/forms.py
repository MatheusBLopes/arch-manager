from django import forms
from django.utils.text import slugify

from .models import Project, ProjectDocumentation


def _get_unique_slug(model, name, instance=None):
    """Gera slug único a partir do nome."""
    base = slugify(name) or "untitled"
    slug = base
    counter = 1
    qs = model.objects.filter(slug=slug)
    if instance and instance.pk:
        qs = qs.exclude(pk=instance.pk)
    while qs.exists():
        slug = f"{base}-{counter}"
        counter += 1
        qs = model.objects.filter(slug=slug)
        if instance and instance.pk:
            qs = qs.exclude(pk=instance.pk)
    return slug


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "short_description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "short_description": forms.Textarea(
                attrs={"rows": 3, "class": "form-control"}
            ),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.slug = _get_unique_slug(Project, instance.name, instance)
        if commit:
            instance.save()
        return instance


class ProjectDocumentationForm(forms.ModelForm):
    class Meta:
        model = ProjectDocumentation
        fields = ["title", "markdown_content"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "markdown_content": forms.Textarea(
                attrs={
                    "rows": 20,
                    "class": "form-control font-monospace",
                    "placeholder": "Escreva a documentação do projeto em Markdown...\n\n# Visão Geral\n\n## Objetivos\n\n- Item 1\n- Item 2",
                }
            ),
        }
