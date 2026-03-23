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

    def test_resource_update_get(self, client):
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        r = Resource.objects.create(
            name="upd",
            slug="upd",
            resource_type=rt,
            short_description="X",
        )
        response = client.get(reverse("resources:update", kwargs={"slug": r.slug}))
        assert response.status_code == 200

    def test_resource_update_post(self, client):
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        r = Resource.objects.create(
            name="upd",
            slug="upd",
            resource_type=rt,
            short_description="X",
        )
        response = client.post(
            reverse("resources:update", kwargs={"slug": r.slug}),
            {
                "name": "upd",
                "slug": "upd",
                "resource_type": rt.pk,
                "short_description": "Desc atualizada",
            },
        )
        assert response.status_code == 302
        r.refresh_from_db()
        assert r.short_description == "Desc atualizada"

    def test_resource_update_lambda_with_details(self, client):
        """Atualiza recurso Lambda com LambdaDetails."""
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        r = Resource.objects.create(
            name="lambda-upd",
            slug="lambda-upd",
            resource_type=rt,
            short_description="Lambda",
        )
        from .models import LambdaDetails

        LambdaDetails.objects.create(resource=r, runtime_version="python3.11")
        response = client.post(
            reverse("resources:update", kwargs={"slug": r.slug}),
            {
                "name": "lambda-upd",
                "resource_type": rt.pk,
                "short_description": "Lambda",
                "runtime_version": "python3.12",
                "example_invocation_payload": '{"x":1}',
                "mermaid_diagram": "graph A-->B",
            },
        )
        assert response.status_code == 302
        r.lambda_details.refresh_from_db()
        assert r.lambda_details.runtime_version == "python3.12"

    def test_resource_delete_post(self, client):
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        r = Resource.objects.create(
            name="del",
            slug="del",
            resource_type=rt,
            short_description="X",
        )
        response = client.post(reverse("resources:delete", kwargs={"slug": r.slug}))
        assert response.status_code == 302
        assert not Resource.objects.filter(pk=r.pk).exists()

    def test_resource_delete_get_redirects(self, client):
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        r = Resource.objects.create(
            name="del",
            slug="del",
            resource_type=rt,
            short_description="X",
        )
        response = client.get(reverse("resources:delete", kwargs={"slug": r.slug}))
        assert response.status_code == 302

    def test_resource_create_with_type_param(self, client):
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        response = client.get(reverse("resources:create") + "?type=lambda")
        assert response.status_code == 200

    def test_resource_create_lambda_with_details(self, client):
        """Cria recurso Lambda com LambdaDetails (runtime, payload, mermaid)."""
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        response = client.post(
            reverse("resources:create"),
            {
                "name": "my-lambda",
                "slug": "my-lambda",
                "resource_type": rt.pk,
                "short_description": "Lambda",
                "runtime_version": "python3.12",
                "example_invocation_payload": "{}",
                "mermaid_diagram": "graph A-->B",
            },
        )
        assert response.status_code == 302
        r = Resource.objects.get(slug="my-lambda")
        assert r.lambda_details.runtime_version == "python3.12"


@pytest.mark.django_db
class TestResourceForms:
    def test_resource_form_valid(self):
        from .forms import ResourceForm

        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        form = ResourceForm(
            data={
                "name": "new-lambda",
                "resource_type": rt.pk,
                "short_description": "Descrição",
            }
        )
        assert form.is_valid()

    def test_resource_form_unique_slug_on_collision(self):
        """Exercita _get_unique_slug quando slug já existe."""
        from .forms import ResourceForm

        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        Resource.objects.create(name="my-fn", slug="my-fn", resource_type=rt, short_description="X")
        form = ResourceForm(
            data={
                "name": "my-fn",
                "resource_type": rt.pk,
                "short_description": "Outra",
            }
        )
        assert form.is_valid()
        r = form.save()
        assert r.slug.startswith("my-fn-")
        assert r.slug != "my-fn"

    def test_resource_form_with_project(self):
        from .forms import ResourceForm
        from arch_manager.apps.projects.models import Project

        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        p = Project.objects.create(name="P", slug="p", short_description="X")
        form = ResourceForm(
            data={
                "name": "r",
                "resource_type": rt.pk,
                "short_description": "Desc",
                "project": p.pk,
            }
        )
        assert form.is_valid()
        r = form.save()
        assert r.project == p


@pytest.mark.django_db
class TestResourceIsDatabase:
    def test_is_database_true_for_rds(self):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        assert r.is_database() is True

    def test_is_database_true_for_dynamodb(self):
        rt = ResourceType.objects.create(name="DynamoDB", slug="dynamodb-table")
        r = Resource.objects.create(name="table", slug="table", resource_type=rt, short_description="Table")
        assert r.is_database() is True

    def test_is_database_false_for_lambda(self):
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        r = Resource.objects.create(name="fn", slug="fn", resource_type=rt, short_description="Function")
        assert r.is_database() is False


@pytest.mark.django_db
class TestDatabaseModels:
    def test_database_table_creation(self):
        from .models import DatabaseTable

        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        table = DatabaseTable.objects.create(resource=r, name="users", description="Tabela de usuários")
        assert table.name == "users"
        assert str(table) == "users (db)"

    def test_table_field_creation(self):
        from .models import DatabaseTable, TableField

        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        table = DatabaseTable.objects.create(resource=r, name="users")
        field = TableField.objects.create(table=table, name="id", data_type="INT", is_primary_key=True)
        assert field.name == "id"
        assert str(field) == "users.id"

    def test_table_relationship_creation(self):
        from .models import DatabaseTable, TableRelationship

        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        t1 = DatabaseTable.objects.create(resource=r, name="users")
        t2 = DatabaseTable.objects.create(resource=r, name="orders")
        rel = TableRelationship.objects.create(source_table=t1, target_table=t2, relationship_type="one_to_many")
        assert rel.relationship_type == "one_to_many"

    def test_database_query_creation(self):
        from .models import DatabaseQuery

        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        query = DatabaseQuery.objects.create(
            resource=r, name="Listar ativos", description="Retorna usuários ativos", query_text="SELECT * FROM users"
        )
        assert query.name == "Listar ativos"
        assert "SELECT" in query.query_text


@pytest.mark.django_db
class TestDatabaseViews:
    def test_database_tables_requires_database_resource(self, client):
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        r = Resource.objects.create(name="fn", slug="fn", resource_type=rt, short_description="Fn")
        response = client.get(reverse("resources:database-tables", kwargs={"slug": r.slug}))
        assert response.status_code == 302
        assert "fn" in response.url

    def test_database_tables_responds_200_for_rds(self, client):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        response = client.get(reverse("resources:database-tables", kwargs={"slug": r.slug}))
        assert response.status_code == 200

    def test_database_table_create(self, client):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        response = client.post(
            reverse("resources:database-table-create", kwargs={"slug": r.slug}),
            {"name": "users", "description": "Tabela users", "order": 0},
        )
        assert response.status_code == 302
        from .models import DatabaseTable

        assert DatabaseTable.objects.filter(resource=r, name="users").exists()

    def test_database_query_create(self, client):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        response = client.post(
            reverse("resources:database-query-create", kwargs={"slug": r.slug}),
            {
                "name": "Query útil",
                "description": "Lista registros ativos",
                "query_text": "SELECT * FROM users WHERE active=1",
                "order": 0,
            },
        )
        assert response.status_code == 302
        from .models import DatabaseQuery

        assert DatabaseQuery.objects.filter(resource=r, name="Query útil").exists()

    def test_database_table_detail(self, client):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        from .models import DatabaseTable

        table = DatabaseTable.objects.create(resource=r, name="users")
        response = client.get(
            reverse("resources:database-table-detail", kwargs={"slug": r.slug, "pk": table.pk})
        )
        assert response.status_code == 200

    def test_database_table_update(self, client):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        from .models import DatabaseTable

        table = DatabaseTable.objects.create(resource=r, name="users")
        response = client.post(
            reverse("resources:database-table-update", kwargs={"slug": r.slug, "pk": table.pk}),
            {"name": "users_v2", "description": "Tabela atualizada", "order": 0},
        )
        assert response.status_code == 302
        table.refresh_from_db()
        assert table.name == "users_v2"

    def test_database_table_delete(self, client):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        from .models import DatabaseTable

        table = DatabaseTable.objects.create(resource=r, name="users")
        response = client.post(
            reverse("resources:database-table-delete", kwargs={"slug": r.slug, "pk": table.pk})
        )
        assert response.status_code == 302
        assert not DatabaseTable.objects.filter(pk=table.pk).exists()

    def test_database_field_create_get(self, client):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        from .models import DatabaseTable

        table = DatabaseTable.objects.create(resource=r, name="users")
        response = client.get(
            reverse("resources:database-field-create", kwargs={"slug": r.slug, "table_pk": table.pk})
        )
        assert response.status_code == 200

    def test_database_field_create(self, client):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        from .models import DatabaseTable

        table = DatabaseTable.objects.create(resource=r, name="users")
        response = client.post(
            reverse("resources:database-field-create", kwargs={"slug": r.slug, "table_pk": table.pk}),
            {
                "name": "email",
                "data_type": "VARCHAR(255)",
                "is_primary_key": False,
                "is_nullable": True,
                "description": "",
                "order": 0,
            },
        )
        assert response.status_code == 302
        assert table.fields.filter(name="email").exists()

    def test_database_relationship_list(self, client):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        response = client.get(
            reverse("resources:database-relationships", kwargs={"slug": r.slug})
        )
        assert response.status_code == 200

    def test_database_relationship_create(self, client):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        from .models import DatabaseTable, TableRelationship

        t1 = DatabaseTable.objects.create(resource=r, name="users")
        t2 = DatabaseTable.objects.create(resource=r, name="orders")
        response = client.post(
            reverse("resources:database-relationship-create", kwargs={"slug": r.slug}),
            {"source_table": t1.pk, "target_table": t2.pk, "relationship_type": "one_to_many"},
        )
        assert response.status_code == 302
        assert TableRelationship.objects.filter(source_table=t1, target_table=t2).exists()

    def test_database_query_update(self, client):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        from .models import DatabaseQuery

        q = DatabaseQuery.objects.create(
            resource=r, name="Q1", query_text="SELECT 1", order=0
        )
        response = client.post(
            reverse("resources:database-query-update", kwargs={"slug": r.slug, "pk": q.pk}),
            {"name": "Q1 Updated", "description": "Desc", "query_text": "SELECT 2", "order": 0},
        )
        assert response.status_code == 302
        q.refresh_from_db()
        assert q.name == "Q1 Updated"


@pytest.mark.django_db
class TestResourceTypeViews:
    def test_resource_type_list(self, client):
        response = client.get(reverse("resources:type-list"))
        assert response.status_code == 200

    def test_resource_type_create_get(self, client):
        response = client.get(reverse("resources:type-create"))
        assert response.status_code == 200

    def test_resource_type_create_post(self, client):
        response = client.post(
            reverse("resources:type-create"),
            {"name": "Novo Tipo", "slug": "novo-tipo", "description": "Desc"},
        )
        assert response.status_code == 302
        assert ResourceType.objects.filter(slug="novo-tipo").exists()

    def test_resource_type_update(self, client):
        rt = ResourceType.objects.create(name="Tipo", slug="tipo", description="X")
        response = client.post(
            reverse("resources:type-update", kwargs={"slug": rt.slug}),
            {"name": "Tipo Atualizado", "slug": "tipo", "description": "Y"},
        )
        assert response.status_code == 302
        rt.refresh_from_db()
        assert rt.name == "Tipo Atualizado"

    def test_resource_type_delete_without_resources(self, client):
        rt = ResourceType.objects.create(name="Vazio", slug="vazio")
        response = client.post(reverse("resources:type-delete", kwargs={"slug": rt.slug}))
        assert response.status_code == 302
        assert not ResourceType.objects.filter(pk=rt.pk).exists()

    def test_resource_type_delete_get_redirects(self, client):
        rt = ResourceType.objects.create(name="Vazio", slug="vazio")
        response = client.get(reverse("resources:type-delete", kwargs={"slug": rt.slug}))
        assert response.status_code == 302

    def test_resource_type_delete_with_resources_blocks(self, client):
        rt = ResourceType.objects.create(name="Usado", slug="usado")
        Resource.objects.create(
            name="r", slug="r", resource_type=rt, short_description="X"
        )
        response = client.post(reverse("resources:type-delete", kwargs={"slug": rt.slug}))
        assert response.status_code == 302
        assert ResourceType.objects.filter(pk=rt.pk).exists()


@pytest.mark.django_db
class TestApiGatewayViews:
    def test_api_endpoint_list_requires_api_gateway(self, client):
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        r = Resource.objects.create(name="fn", slug="fn", resource_type=rt, short_description="X")
        response = client.get(
            reverse("resources:api-endpoint-list", kwargs={"slug": r.slug})
        )
        assert response.status_code == 302

    def test_api_endpoint_list(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        response = client.get(
            reverse("resources:api-endpoint-list", kwargs={"slug": r.slug})
        )
        assert response.status_code == 200

    def test_api_endpoint_create(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        response = client.post(
            reverse("resources:api-endpoint-create", kwargs={"slug": r.slug}),
            {"path": "/users", "description": "Lista usuários", "order": 0},
        )
        assert response.status_code == 302
        from .models import ApiGatewayEndpoint

        assert ApiGatewayEndpoint.objects.filter(resource=r, path="/users").exists()

    def test_api_endpoint_detail(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        response = client.get(
            reverse("resources:api-endpoint-detail", kwargs={"slug": r.slug, "pk": ep.pk})
        )
        assert response.status_code == 200

    def test_api_endpoint_update(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        response = client.post(
            reverse("resources:api-endpoint-update", kwargs={"slug": r.slug, "pk": ep.pk}),
            {"path": "/users/v2", "description": "Atualizado", "order": 0},
        )
        assert response.status_code == 302
        ep.refresh_from_db()
        assert ep.path == "/users/v2"

    def test_api_endpoint_delete(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        response = client.post(
            reverse("resources:api-endpoint-delete", kwargs={"slug": r.slug, "pk": ep.pk})
        )
        assert response.status_code == 302
        assert not ApiGatewayEndpoint.objects.filter(pk=ep.pk).exists()

    def test_api_method_create_get(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        response = client.get(
            reverse(
                "resources:api-method-create",
                kwargs={"slug": r.slug, "endpoint_pk": ep.pk},
            )
        )
        assert response.status_code == 200

    def test_api_method_create(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        response = client.post(
            reverse("resources:api-method-create", kwargs={"slug": r.slug, "endpoint_pk": ep.pk}),
            {"http_method": "GET", "description": "List", "order": 0},
        )
        assert response.status_code == 302
        assert ApiGatewayEndpointMethod.objects.filter(endpoint=ep, http_method="GET").exists()

    def test_database_relationship_update_get(self, client):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        from .models import DatabaseTable, TableRelationship

        t1 = DatabaseTable.objects.create(resource=r, name="users")
        t2 = DatabaseTable.objects.create(resource=r, name="orders")
        rel = TableRelationship.objects.create(
            source_table=t1, target_table=t2, relationship_type="one_to_many"
        )
        response = client.get(
            reverse("resources:database-relationship-update", kwargs={"slug": r.slug, "pk": rel.pk})
        )
        assert response.status_code == 200

    def test_database_relationship_update(self, client):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        from .models import DatabaseTable, TableRelationship

        t1 = DatabaseTable.objects.create(resource=r, name="users")
        t2 = DatabaseTable.objects.create(resource=r, name="orders")
        rel = TableRelationship.objects.create(
            source_table=t1, target_table=t2, relationship_type="one_to_many"
        )
        response = client.post(
            reverse("resources:database-relationship-update", kwargs={"slug": r.slug, "pk": rel.pk}),
            {"source_table": t1.pk, "target_table": t2.pk, "relationship_type": "many_to_one"},
        )
        assert response.status_code == 302
        rel.refresh_from_db()
        assert rel.relationship_type == "many_to_one"

    def test_database_relationship_delete(self, client):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        from .models import DatabaseTable, TableRelationship

        t1 = DatabaseTable.objects.create(resource=r, name="users")
        t2 = DatabaseTable.objects.create(resource=r, name="orders")
        rel = TableRelationship.objects.create(
            source_table=t1, target_table=t2, relationship_type="one_to_many"
        )
        response = client.post(
            reverse("resources:database-relationship-delete", kwargs={"slug": r.slug, "pk": rel.pk})
        )
        assert response.status_code == 302
        assert not TableRelationship.objects.filter(pk=rel.pk).exists()

    def test_database_query_delete(self, client):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        from .models import DatabaseQuery

        q = DatabaseQuery.objects.create(resource=r, name="Q1", query_text="SELECT 1", order=0)
        response = client.post(
            reverse("resources:database-query-delete", kwargs={"slug": r.slug, "pk": q.pk})
        )
        assert response.status_code == 302
        assert not DatabaseQuery.objects.filter(pk=q.pk).exists()

    def test_database_field_update(self, client):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        from .models import DatabaseTable, TableField

        table = DatabaseTable.objects.create(resource=r, name="users")
        field = TableField.objects.create(
            table=table, name="email", data_type="VARCHAR", order=0
        )
        response = client.post(
            reverse(
                "resources:database-field-update",
                kwargs={"slug": r.slug, "table_pk": table.pk, "pk": field.pk},
            ),
            {
                "name": "email",
                "data_type": "VARCHAR(255)",
                "is_primary_key": False,
                "is_nullable": True,
                "description": "Email do user",
                "order": 0,
            },
        )
        assert response.status_code == 302
        field.refresh_from_db()
        assert field.data_type == "VARCHAR(255)"

    def test_database_field_delete(self, client):
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        from .models import DatabaseTable, TableField

        table = DatabaseTable.objects.create(resource=r, name="users")
        field = TableField.objects.create(
            table=table, name="email", data_type="VARCHAR", order=0
        )
        response = client.post(
            reverse(
                "resources:database-field-delete",
                kwargs={"slug": r.slug, "table_pk": table.pk, "pk": field.pk},
            )
        )
        assert response.status_code == 302
        assert not TableField.objects.filter(pk=field.pk).exists()

    def test_api_method_update(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="GET")
        response = client.post(
            reverse(
                "resources:api-method-update",
                kwargs={"slug": r.slug, "endpoint_pk": ep.pk, "pk": m.pk},
            ),
            {"http_method": "POST", "description": "Create", "order": 0},
        )
        assert response.status_code == 302
        m.refresh_from_db()
        assert m.http_method == "POST"

    def test_api_method_delete(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="GET")
        response = client.post(
            reverse(
                "resources:api-method-delete",
                kwargs={"slug": r.slug, "endpoint_pk": ep.pk, "pk": m.pk},
            )
        )
        assert response.status_code == 302
        assert not ApiGatewayEndpointMethod.objects.filter(pk=m.pk).exists()

    def test_api_parameter_create_get(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="GET")
        response = client.get(
            reverse(
                "resources:api-parameter-create",
                kwargs={"slug": r.slug, "endpoint_pk": ep.pk, "method_pk": m.pk},
            )
        )
        assert response.status_code == 200

    def test_api_parameter_create(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod, ApiGatewayParameter

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="GET")
        response = client.post(
            reverse(
                "resources:api-parameter-create",
                kwargs={"slug": r.slug, "endpoint_pk": ep.pk, "method_pk": m.pk},
            ),
            {"name": "id", "param_in": "path", "param_type": "integer", "required": True, "description": "", "order": 0},
        )
        assert response.status_code == 302
        assert ApiGatewayParameter.objects.filter(method=m, name="id").exists()

    def test_api_parameter_update(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod, ApiGatewayParameter

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="GET")
        p = ApiGatewayParameter.objects.create(method=m, name="id", param_in="path")
        response = client.post(
            reverse(
                "resources:api-parameter-update",
                kwargs={"slug": r.slug, "endpoint_pk": ep.pk, "method_pk": m.pk, "pk": p.pk},
            ),
            {"name": "id", "param_in": "path", "param_type": "string", "required": False, "description": "Updated", "order": 0},
        )
        assert response.status_code == 302
        p.refresh_from_db()
        assert p.description == "Updated"

    def test_api_parameter_delete(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod, ApiGatewayParameter

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="GET")
        p = ApiGatewayParameter.objects.create(method=m, name="id", param_in="path")
        response = client.post(
            reverse(
                "resources:api-parameter-delete",
                kwargs={"slug": r.slug, "endpoint_pk": ep.pk, "method_pk": m.pk, "pk": p.pk},
            )
        )
        assert response.status_code == 302
        assert not ApiGatewayParameter.objects.filter(pk=p.pk).exists()

    def test_api_payload_create_get(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="POST")
        response = client.get(
            reverse(
                "resources:api-payload-create",
                kwargs={"slug": r.slug, "endpoint_pk": ep.pk, "method_pk": m.pk},
            )
        )
        assert response.status_code == 200

    def test_api_payload_create(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod, ApiGatewayPayload

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="POST")
        response = client.post(
            reverse(
                "resources:api-payload-create",
                kwargs={"slug": r.slug, "endpoint_pk": ep.pk, "method_pk": m.pk},
            ),
            {"direction": "request", "content_type": "application/json", "body": "{}", "order": 0},
        )
        assert response.status_code == 302
        assert ApiGatewayPayload.objects.filter(method=m, direction="request").exists()

    def test_api_payload_update(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod, ApiGatewayPayload

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="POST")
        pl = ApiGatewayPayload.objects.create(method=m, direction="request", content_type="application/json", body="{}")
        response = client.post(
            reverse(
                "resources:api-payload-update",
                kwargs={"slug": r.slug, "endpoint_pk": ep.pk, "method_pk": m.pk, "pk": pl.pk},
            ),
            {"direction": "request", "content_type": "application/json", "body": '{"updated": true}', "order": 0},
        )
        assert response.status_code == 302
        pl.refresh_from_db()
        assert "updated" in pl.body

    def test_api_payload_delete(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod, ApiGatewayPayload

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="POST")
        pl = ApiGatewayPayload.objects.create(method=m, direction="request", content_type="application/json")
        response = client.post(
            reverse(
                "resources:api-payload-delete",
                kwargs={"slug": r.slug, "endpoint_pk": ep.pk, "method_pk": m.pk, "pk": pl.pk},
            )
        )
        assert response.status_code == 302
        assert not ApiGatewayPayload.objects.filter(pk=pl.pk).exists()

    def test_api_invocation_create_get(self, client):
        rt_api = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt_api, short_description="API")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="POST")
        response = client.get(
            reverse(
                "resources:api-invocation-create",
                kwargs={"slug": r.slug, "endpoint_pk": ep.pk, "method_pk": m.pk},
            )
        )
        assert response.status_code == 200

    def test_api_invocation_create(self, client):
        rt_api = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        rt_lam = ResourceType.objects.create(name="Lambda", slug="lambda")
        r_api = Resource.objects.create(name="api", slug="api", resource_type=rt_api, short_description="API")
        r_lam = Resource.objects.create(name="fn", slug="fn", resource_type=rt_lam, short_description="Lambda")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod, ApiGatewayInvocation

        ep = ApiGatewayEndpoint.objects.create(resource=r_api, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="POST")
        response = client.post(
            reverse(
                "resources:api-invocation-create",
                kwargs={"slug": r_api.slug, "endpoint_pk": ep.pk, "method_pk": m.pk},
            ),
            {"target_resource": r_lam.pk, "description": "Invokes Lambda", "order": 0},
        )
        assert response.status_code == 302
        assert ApiGatewayInvocation.objects.filter(method=m, target_resource=r_lam).exists()

    def test_api_invocation_update(self, client):
        rt_api = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        rt_lam = ResourceType.objects.create(name="Lambda", slug="lambda")
        r_api = Resource.objects.create(name="api", slug="api", resource_type=rt_api, short_description="API")
        r_lam = Resource.objects.create(name="fn", slug="fn", resource_type=rt_lam, short_description="Lambda")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod, ApiGatewayInvocation

        ep = ApiGatewayEndpoint.objects.create(resource=r_api, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="POST")
        inv = ApiGatewayInvocation.objects.create(method=m, target_resource=r_lam, description="Old")
        response = client.post(
            reverse(
                "resources:api-invocation-update",
                kwargs={"slug": r_api.slug, "endpoint_pk": ep.pk, "method_pk": m.pk, "pk": inv.pk},
            ),
            {"target_resource": r_lam.pk, "description": "Updated desc", "order": 0},
        )
        assert response.status_code == 302
        inv.refresh_from_db()
        assert inv.description == "Updated desc"

    def test_api_invocation_delete(self, client):
        rt_api = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        rt_lam = ResourceType.objects.create(name="Lambda", slug="lambda")
        r_api = Resource.objects.create(name="api", slug="api", resource_type=rt_api, short_description="API")
        r_lam = Resource.objects.create(name="fn", slug="fn", resource_type=rt_lam, short_description="Lambda")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod, ApiGatewayInvocation

        ep = ApiGatewayEndpoint.objects.create(resource=r_api, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="POST")
        inv = ApiGatewayInvocation.objects.create(method=m, target_resource=r_lam)
        response = client.post(
            reverse(
                "resources:api-invocation-delete",
                kwargs={"slug": r_api.slug, "endpoint_pk": ep.pk, "method_pk": m.pk, "pk": inv.pk},
            )
        )
        assert response.status_code == 302
        assert not ApiGatewayInvocation.objects.filter(pk=inv.pk).exists()

    def test_api_example_curl_create_get(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="GET")
        response = client.get(
            reverse(
                "resources:api-example-curl-create",
                kwargs={"slug": r.slug, "endpoint_pk": ep.pk, "method_pk": m.pk},
            )
        )
        assert response.status_code == 200

    def test_api_example_curl_create(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod, ApiGatewayExampleCurl

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="GET")
        response = client.post(
            reverse(
                "resources:api-example-curl-create",
                kwargs={"slug": r.slug, "endpoint_pk": ep.pk, "method_pk": m.pk},
            ),
            {"label": "List users", "curl_command": "curl https://api.example.com/users", "order": 0},
        )
        assert response.status_code == 302
        assert ApiGatewayExampleCurl.objects.filter(method=m, label="List users").exists()

    def test_api_example_curl_update(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod, ApiGatewayExampleCurl

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="GET")
        curl = ApiGatewayExampleCurl.objects.create(method=m, label="Old", curl_command="curl x")
        response = client.post(
            reverse(
                "resources:api-example-curl-update",
                kwargs={"slug": r.slug, "endpoint_pk": ep.pk, "method_pk": m.pk, "pk": curl.pk},
            ),
            {"label": "Updated label", "curl_command": "curl https://api.example.com/users", "order": 0},
        )
        assert response.status_code == 302
        curl.refresh_from_db()
        assert curl.label == "Updated label"

    def test_api_example_curl_delete(self, client):
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(name="api", slug="api", resource_type=rt, short_description="API")
        from .models import ApiGatewayEndpoint, ApiGatewayEndpointMethod, ApiGatewayExampleCurl

        ep = ApiGatewayEndpoint.objects.create(resource=r, path="/users")
        m = ApiGatewayEndpointMethod.objects.create(endpoint=ep, http_method="GET")
        curl = ApiGatewayExampleCurl.objects.create(method=m, label="Test", curl_command="curl x")
        response = client.post(
            reverse(
                "resources:api-example-curl-delete",
                kwargs={"slug": r.slug, "endpoint_pk": ep.pk, "method_pk": m.pk, "pk": curl.pk},
            )
        )
        assert response.status_code == 302
        assert not ApiGatewayExampleCurl.objects.filter(pk=curl.pk).exists()


@pytest.mark.django_db
class TestTableRelationshipFormValidation:
    def test_cannot_relate_table_to_itself(self):
        from .forms import TableRelationshipForm
        from .models import DatabaseTable

        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(name="db", slug="db", resource_type=rt, short_description="DB")
        table = DatabaseTable.objects.create(resource=r, name="users")
        form = TableRelationshipForm(
            data={
                "source_table": table.pk,
                "target_table": table.pk,
                "relationship_type": "one_to_many",
            },
            resource=r,
        )
        assert form.is_valid() is False

    def test_cannot_relate_tables_from_different_resources(self):
        """Exercita o clean quando tabelas são de recursos diferentes."""
        from .forms import TableRelationshipForm
        from .models import DatabaseTable

        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r1 = Resource.objects.create(name="db1", slug="db1", resource_type=rt, short_description="DB1")
        r2 = Resource.objects.create(name="db2", slug="db2", resource_type=rt, short_description="DB2")
        t1 = DatabaseTable.objects.create(resource=r1, name="users")
        t2 = DatabaseTable.objects.create(resource=r2, name="orders")
        form = TableRelationshipForm(
            data={
                "source_table": t1.pk,
                "target_table": t2.pk,
                "relationship_type": "one_to_many",
            },
            resource=r1,
        )
        # Form precisa ter ambos os tables no queryset - vamos criar com resource=r1
        # e injetar t2 manualmente (t2 está em r2). O queryset de target_table
        # é filtrado por resource, então t2 não estaria. Precisamos de outra abordagem.
        # Na prática, o usuário não pode escolher t2 no dropdown. Mas podemos
        # chamar form.clean() com dados que passam source_table e target_table
        # de recursos diferentes - isso requer que o queryset permita. O form
        # __init__ com resource=r1 define queryset como tables de r1 apenas.
        # Então target_table choices não incluiria t2. Ao submeter t2.pk,
        # Django pode invalidar por "choice inválido" antes do clean.
        # Vamos tentar: criar form sem resource para ter queryset amplo?
        form = TableRelationshipForm(
            data={
                "source_table": t1.pk,
                "target_table": t2.pk,
                "relationship_type": "one_to_many",
            },
        )
        # Sem resource, o queryset é o default (todas as tabelas). O clean
        # deve pegar source e target e verificar source.resource != target.resource.
        assert form.is_valid() is False
        assert "mesmo" in str(form.errors).lower() or "banco" in str(form.errors).lower()
