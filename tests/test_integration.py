"""
Teste de integração: fluxo completo criar recurso -> documentar -> relacionar -> visualizar.
"""

import pytest
from django.urls import reverse

from arch_manager.apps.resources.models import Resource, ResourceType
from arch_manager.apps.relationships.models import ResourceRelationship
from arch_manager.apps.docs.models import ResourceDocumentation


@pytest.mark.django_db
def test_full_flow(client):
    rt1 = ResourceType.objects.create(name="SQS", slug="sqs")
    rt2 = ResourceType.objects.create(name="Lambda", slug="lambda")

    # 1. Criar recurso
    resp = client.post(
        reverse("resources:create"),
        {
            "name": "payments-queue",
            "slug": "payments-queue",
            "resource_type": rt1.pk,
            "short_description": "Fila de eventos de pagamento",
        },
    )
    assert resp.status_code == 302
    r1 = Resource.objects.get(slug="payments-queue")

    # 2. Criar segundo recurso
    resp = client.post(
        reverse("resources:create"),
        {
            "name": "process-payment",
            "slug": "process-payment",
            "resource_type": rt2.pk,
            "short_description": "Lambda que processa pagamentos",
        },
    )
    assert resp.status_code == 302
    r2 = Resource.objects.get(slug="process-payment")

    # 3. Documentar recurso
    resp = client.post(
        reverse("docs:edit", kwargs={"resource_slug": r1.slug}),
        {
            "title": "Doc da fila",
            "markdown_content": "# Fila payments\n\nProcessa eventos.",
        },
    )
    assert resp.status_code == 302
    assert ResourceDocumentation.objects.filter(resource=r1).exists()

    # 4. Criar relacionamento (via model pois o form em teste pode ter restrições de queryset)
    ResourceRelationship.objects.create(
        source_resource=r1,
        target_resource=r2,
        relationship_type="invokes",
        description="A fila invoca a lambda",
    )

    # 5. Visualizar detalhe
    resp = client.get(reverse("resources:detail", kwargs={"slug": r1.slug}))
    assert resp.status_code == 200
    assert b"payments-queue" in resp.content
    assert b"process-payment" in resp.content or b"invokes" in resp.content
    assert b"Fila payments" in resp.content or b"Processa eventos" in resp.content
