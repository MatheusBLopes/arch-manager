from django import forms
from django.utils.text import slugify

from .models import Resource, ResourceType


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = [
            "name",
            "slug",
            "resource_type",
            "short_description",
            "detailed_description",
            "service_name",
            "environment",
            "region",
            "identifier",
            "endpoint_or_path",
            "status",
            "notes",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "resource_type": forms.Select(attrs={"class": "form-select"}),
            "short_description": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "detailed_description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "service_name": forms.TextInput(attrs={"class": "form-control"}),
            "environment": forms.TextInput(attrs={"class": "form-control"}),
            "region": forms.TextInput(attrs={"class": "form-control"}),
            "identifier": forms.TextInput(attrs={"class": "form-control"}),
            "endpoint_or_path": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
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
