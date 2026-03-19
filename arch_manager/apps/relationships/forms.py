from django import forms
from django.core.exceptions import ValidationError

from arch_manager.apps.resources.models import Resource

from .models import ResourceRelationship


class ResourceRelationshipForm(forms.ModelForm):
    class Meta:
        model = ResourceRelationship
        fields = [
            "source_resource",
            "target_resource",
            "relationship_type",
            "description",
            "is_active",
        ]
        widgets = {
            "source_resource": forms.Select(attrs={"class": "form-select"}),
            "target_resource": forms.Select(attrs={"class": "form-select"}),
            "relationship_type": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Resource.objects.filter(is_active=True).select_related("resource_type")
        self.fields["source_resource"].queryset = qs
        self.fields["target_resource"].queryset = qs

    def clean(self):
        cleaned_data = super().clean()
        source = cleaned_data.get("source_resource")
        target = cleaned_data.get("target_resource")

        if source and target and source == target:
            raise ValidationError("Origem e destino não podem ser o mesmo recurso.")

        return cleaned_data
