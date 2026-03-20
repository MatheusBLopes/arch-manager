from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from arch_manager.apps.projects.models import Project

from .models import (
    ApiGatewayEndpoint,
    ApiGatewayEndpointMethod,
    ApiGatewayExampleCurl,
    ApiGatewayInvocation,
    ApiGatewayParameter,
    ApiGatewayPayload,
    DatabaseQuery,
    DatabaseTable,
    Resource,
    ResourceType,
    TableField,
    TableRelationship,
)


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


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = [
            "name",
            "resource_type",
            "project",
            "short_description",
            "detailed_description",
            "runtime_version",
            "repository_url",
            "has_pentest",
            "notes",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "resource_type": forms.Select(attrs={"class": "form-select"}),
            "project": forms.Select(attrs={"class": "form-select"}),
            "short_description": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "detailed_description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "runtime_version": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: python3.12.0, nodejs20.x",
                }
            ),
            "repository_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://github.com/..."}),
            "has_pentest": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["resource_type"].queryset = ResourceType.objects.filter(is_active=True)
        self.fields["project"].queryset = Project.objects.all()
        self.fields["project"].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.slug = _get_unique_slug(Resource, instance.name, instance)
        if commit:
            instance.save()
        return instance


class ResourceTypeForm(forms.ModelForm):
    class Meta:
        model = ResourceType
        fields = ["name", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.slug = _get_unique_slug(ResourceType, instance.name, instance)
        if commit:
            instance.save()
        return instance


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


# --- API Gateway forms ---


class ApiGatewayEndpointForm(forms.ModelForm):
    class Meta:
        model = ApiGatewayEndpoint
        fields = ["path", "description", "order"]
        widgets = {
            "path": forms.TextInput(attrs={"class": "form-control", "placeholder": "/users, /orders/{id}"}),
            "description": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class ApiGatewayEndpointMethodForm(forms.ModelForm):
    class Meta:
        model = ApiGatewayEndpointMethod
        fields = ["http_method", "description", "order"]
        widgets = {
            "http_method": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class ApiGatewayParameterForm(forms.ModelForm):
    class Meta:
        model = ApiGatewayParameter
        fields = ["name", "param_in", "param_type", "required", "description", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "param_in": forms.Select(attrs={"class": "form-select"}),
            "param_type": forms.TextInput(attrs={"class": "form-control", "placeholder": "string, integer, boolean"}),
            "required": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "description": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class ApiGatewayPayloadForm(forms.ModelForm):
    class Meta:
        model = ApiGatewayPayload
        fields = ["direction", "content_type", "body", "order"]
        widgets = {
            "direction": forms.Select(attrs={"class": "form-select"}),
            "content_type": forms.TextInput(attrs={"class": "form-control", "placeholder": "application/json"}),
            "body": forms.Textarea(attrs={"rows": 8, "class": "form-control font-monospace", "placeholder": '{"key": "value"}'}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class ApiGatewayInvocationForm(forms.ModelForm):
    class Meta:
        model = ApiGatewayInvocation
        fields = ["target_resource", "description", "order"]
        widgets = {
            "target_resource": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, resource=None, **kwargs):
        res = kwargs.pop("resource", None) or resource
        super().__init__(*args, **kwargs)
        if res:
            self.fields["target_resource"].queryset = Resource.objects.exclude(pk=res.pk).select_related("resource_type").order_by("name")


class ApiGatewayExampleCurlForm(forms.ModelForm):
    class Meta:
        model = ApiGatewayExampleCurl
        fields = ["label", "curl_command", "order"]
        widgets = {
            "label": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Listar usuários"}),
            "curl_command": forms.Textarea(attrs={"rows": 4, "class": "form-control font-monospace", "placeholder": "curl -X GET https://api.example.com/users"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }
