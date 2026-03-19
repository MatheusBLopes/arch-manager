import pytest
from django.urls import reverse

from .models import Resource, ResourceType


@pytest.mark.django_db
class TestResourceTypeModel:
    def test_create_resource_type(self):
        rt = ResourceType.objects.create(
            name="Lambda",
            slug="lambda",
            description="Função serverless",
        )
        assert rt.name == "Lambda"
        assert str(rt) == "Lambda"

    def test_resource_type_str(self):
        rt = ResourceType.objects.create(name="SQS", slug="sqs")
        assert "SQS" in str(rt)


@pytest.mark.django_db
class TestResourceModel:
    def test_create_resource(self):
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        r = Resource.objects.create(
            name="process-payment",
            slug="process-payment",
            resource_type=rt,
            short_description="Processa pagamentos",
        )
        assert r.name == "process-payment"
        assert "process-payment" in str(r)


@pytest.mark.django_db
class TestResourceViews:
    def test_dashboard_responds_200(self, client):
        response = client.get(reverse("core:dashboard"))
        assert response.status_code == 200

    def test_resource_list_responds_200(self, client):
        response = client.get(reverse("resources:list"))
        assert response.status_code == 200

    def test_resource_list_by_type_responds_200(self, client):
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        response = client.get(
            reverse("resources:by-type", kwargs={"type_slug": rt.slug})
        )
        assert response.status_code == 200

    def test_resource_create_redirects_to_detail(self, client):
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        response = client.post(
            reverse("resources:create"),
            {
                "name": "my-lambda",
                "slug": "my-lambda",
                "resource_type": rt.pk,
                "short_description": "Minha Lambda",
            },
        )
        assert response.status_code == 302
        assert "my-lambda" in response.url

    def test_resource_detail_responds_200(self, client):
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        r = Resource.objects.create(
            name="test-lambda",
            slug="test-lambda",
            resource_type=rt,
            short_description="Lambda de teste",
        )
        response = client.get(
            reverse("resources:detail", kwargs={"slug": r.slug})
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestResourceForms:
    def test_resource_form_valid(self):
        from .forms import ResourceForm

        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        form = ResourceForm(
            data={
                "name": "new-lambda",
                "slug": "new-lambda",
                "resource_type": rt.pk,
                "short_description": "Descrição",
            }
        )
        assert form.is_valid()
