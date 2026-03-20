from django import forms
from django.utils.text import slugify

from .models import Project, ProjectDocumentation


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "slug", "short_description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "short_description": forms.Textarea(
                attrs={"rows": 3, "class": "form-control"}
            ),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        if not slug and self.cleaned_data.get("name"):
            slug = slugify(self.cleaned_data["name"])
        return slug or ""


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
