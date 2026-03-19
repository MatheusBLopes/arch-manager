import pytest
from django.urls import reverse

from arch_manager.apps.resources.models import Resource, ResourceType

from .models import ResourceRelationship


@pytest.fixture
def two_resources(db):
    rt = ResourceType.objects.create(name="Lambda", slug="lambda")
    r1 = Resource.objects.create(
        name="queue",
        slug="queue",
        resource_type=rt,
        short_description="Fila",
    )
    r2 = Resource.objects.create(
        name="lambda",
        slug="lambda-func",
        resource_type=rt,
        short_description="Função",
    )
    return r1, r2


@pytest.mark.django_db
class TestResourceRelationshipModel:
    def test_create_relationship(self, two_resources):
        r1, r2 = two_resources
        rel = ResourceRelationship.objects.create(
            source_resource=r1,
            target_resource=r2,
            relationship_type="invokes",
        )
        assert rel.source_resource == r1
        assert rel.target_resource == r2

    def test_relationship_str(self, two_resources):
        r1, r2 = two_resources
        rel = ResourceRelationship.objects.create(
            source_resource=r1,
            target_resource=r2,
            relationship_type="invokes",
        )
        assert "queue" in str(rel) or "lambda" in str(rel)


@pytest.mark.django_db
class TestResourceRelationshipValidation:
    def test_cannot_relate_resource_to_itself(self, two_resources):
        from .forms import ResourceRelationshipForm

        r1, _ = two_resources
        form = ResourceRelationshipForm(
            data={
                "source_resource": r1.pk,
                "target_resource": r1.pk,
                "relationship_type": "invokes",
            }
        )
        assert not form.is_valid()
        assert "destino" in str(form.errors).lower() or "mesmo" in str(form.errors).lower()


@pytest.mark.django_db
class TestRelationshipViews:
    def test_relationship_create_responds_200(self, client, two_resources):
        response = client.get(reverse("relationships:create"))
        assert response.status_code == 200

    def test_relationship_create_post(self, client, two_resources):
        r1, r2 = two_resources
        response = client.post(
            reverse("relationships:create"),
            {
                "source_resource": r1.pk,
                "target_resource": r2.pk,
                "relationship_type": "invokes",
                "description": "Fila invoca lambda",
            },
        )
        assert response.status_code == 302
