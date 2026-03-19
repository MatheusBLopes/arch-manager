from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .models import (
    DatabaseQuery,
    DatabaseTable,
    Resource,
    ResourceType,
    TableField,
    TableRelationship,
)


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = [
            "name",
            "slug",
            "resource_type",
            "short_description",
            "detailed_description",
            "runtime_version",
            "notes",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "resource_type": forms.Select(attrs={"class": "form-select"}),
            "short_description": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "detailed_description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "runtime_version": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: python3.12.0, nodejs20.x",
                }
            ),
            "notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["resource_type"].queryset = ResourceType.objects.filter(is_active=True)

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        if not slug and self.cleaned_data.get("name"):
            slug = slugify(self.cleaned_data["name"])
        return slug or ""


class ResourceTypeForm(forms.ModelForm):
    class Meta:
        model = ResourceType
        fields = ["name", "slug", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        if not slug:
            slug = slugify(self.cleaned_data.get("name", ""))
        return slug


class DatabaseTableForm(forms.ModelForm):
    class Meta:
        model = DatabaseTable
        fields = ["name", "description", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: users, orders"}),
            "description": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class TableFieldForm(forms.ModelForm):
    class Meta:
        model = TableField
        fields = ["name", "data_type", "is_primary_key", "is_nullable", "description", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: id, email"}),
            "data_type": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: VARCHAR(255), INT"}),
            "is_primary_key": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_nullable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "description": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class TableRelationshipForm(forms.ModelForm):
    class Meta:
        model = TableRelationship
        fields = ["source_table", "target_table", "relationship_type", "source_field", "target_field", "description"]
        widgets = {
            "source_table": forms.Select(attrs={"class": "form-select"}),
            "target_table": forms.Select(attrs={"class": "form-select"}),
            "relationship_type": forms.Select(attrs={"class": "form-select"}),
            "source_field": forms.Select(attrs={"class": "form-select"}),
            "target_field": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

    def __init__(self, *args, resource=None, **kwargs):
        res = resource or (kwargs.get("instance") and kwargs["instance"].source_table.resource)
        kwargs.pop("resource", None)
        super().__init__(*args, **kwargs)
        if res:
            tables = DatabaseTable.objects.filter(resource=res).order_by("order", "name")
            self.fields["source_table"].queryset = tables
            self.fields["target_table"].queryset = tables
            fields_qs = TableField.objects.filter(table__resource=res).select_related("table").order_by("table__order", "table__name", "order", "name")
            self.fields["source_field"].queryset = fields_qs
            self.fields["target_field"].queryset = fields_qs

    def clean(self):
        cleaned = super().clean()
        source = cleaned.get("source_table")
        target = cleaned.get("target_table")
        if source and target and source == target:
            raise ValidationError("Tabela de origem e destino não podem ser a mesma.")
        if source and target and source.resource != target.resource:
            raise ValidationError("As tabelas devem pertencer ao mesmo banco de dados.")
        return cleaned


class DatabaseQueryForm(forms.ModelForm):
    class Meta:
        model = DatabaseQuery
        fields = ["name", "description", "query_text", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Listar usuários ativos"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control", "placeholder": "Descreva quando e por que usar esta query"}),
            "query_text": forms.Textarea(attrs={"rows": 6, "class": "form-control font-monospace", "placeholder": "SELECT * FROM ..."}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }
