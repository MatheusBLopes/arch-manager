from django import forms

from arch_manager.apps.resources.models import Resource

from .models import ResourceDocumentation


class ResourceDocumentationForm(forms.ModelForm):
    class Meta:
        model = ResourceDocumentation
        fields = ["title", "markdown_content"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "markdown_content": forms.Textarea(
                attrs={
                    "rows": 20,
                    "class": "form-control font-monospace",
                    "placeholder": "Escreva sua documentação em Markdown...\n\n# Título\n\n## Subtítulo\n\n- Lista\n- de itens",
                }
            ),
        }
