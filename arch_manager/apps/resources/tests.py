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
