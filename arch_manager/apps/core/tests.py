"""Testes do app core."""

import pytest
from django.urls import reverse

from arch_manager.apps.projects.models import Project, ProjectDocumentation
from arch_manager.apps.resources.models import Resource, ResourceType

from .pdf_export import (
    _format_json,
    _format_sql,
    _break_long_lines,
    build_pdf_buffer,
)


@pytest.mark.django_db
class TestCoreViews:
    def test_dashboard_responds_200(self, client):
        response = client.get(reverse("core:dashboard"))
        assert response.status_code == 200

    def test_pdf_export_responds_200(self, client):
        response = client.get(reverse("core:pdf-export"))
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert "attachment" in response["Content-Disposition"]
        assert b"%PDF" in response.content[:10]


@pytest.mark.django_db
class TestPdfExport:
    def test_build_pdf_buffer_empty(self):
        """PDF vazio (sem projetos nem recursos) deve gerar capa e sumário."""
        result = build_pdf_buffer()
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")
        assert len(result) > 500

    def test_build_pdf_buffer_with_project_and_resource(self):
        """PDF com projeto e recurso."""
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        p = Project.objects.create(
            name="Projeto Teste",
            slug="projeto-teste",
            short_description="Descrição",
        )
        Resource.objects.create(
            name="my-lambda",
            slug="my-lambda",
            resource_type=rt,
            short_description="Lambda de teste",
            project=p,
        )
        result = build_pdf_buffer()
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")
        assert len(result) > 3500  # Com conteúdo deve ser maior que PDF vazio

    def test_build_pdf_buffer_with_documentation(self):
        """PDF com documentação em Markdown."""
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        r = Resource.objects.create(
            name="doc-resource",
            slug="doc-resource",
            resource_type=rt,
            short_description="Com doc",
        )
        from arch_manager.apps.docs.models import ResourceDocumentation

        ResourceDocumentation.objects.create(
            resource=r,
            title="Doc",
            markdown_content="# Título\n\nParágrafo com **negrito**.",
        )
        result = build_pdf_buffer()
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")

    def test_build_pdf_buffer_with_relationships(self):
        """PDF com relacionamentos entre recursos."""
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        r1 = Resource.objects.create(
            name="queue",
            slug="queue",
            resource_type=rt,
            short_description="Fila",
        )
        r2 = Resource.objects.create(
            name="processor",
            slug="processor",
            resource_type=rt,
            short_description="Processador",
        )
        from arch_manager.apps.relationships.models import ResourceRelationship

        ResourceRelationship.objects.create(
            source_resource=r1,
            target_resource=r2,
            relationship_type="invokes",
        )
        result = build_pdf_buffer()
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")

    def test_build_pdf_buffer_with_lambda_details(self):
        """PDF com recurso Lambda que tem runtime, payload e diagrama Mermaid."""
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        r = Resource.objects.create(
            name="lambda-detail",
            slug="lambda-detail",
            resource_type=rt,
            short_description="Lambda com detalhes",
        )
        from arch_manager.apps.resources.models import LambdaDetails

        LambdaDetails.objects.create(
            resource=r,
            runtime_version="python3.12",
            example_invocation_payload='{"event": "test"}',
            mermaid_diagram="graph LR\nA-->B",
        )
        result = build_pdf_buffer()
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")

    def test_build_pdf_buffer_with_database_tables(self):
        """PDF com recurso de banco e tabelas/campos/queries."""
        rt = ResourceType.objects.create(name="RDS", slug="rds-database")
        r = Resource.objects.create(
            name="db-resource",
            slug="db-resource",
            resource_type=rt,
            short_description="Banco com schema",
        )
        from arch_manager.apps.resources.models import (
            DatabaseTable,
            TableField,
            DatabaseQuery,
        )

        table = DatabaseTable.objects.create(
            resource=r, name="users", description="Tabela users"
        )
        TableField.objects.create(
            table=table, name="id", data_type="INT", is_primary_key=True
        )
        DatabaseQuery.objects.create(
            resource=r,
            name="Listar ativos",
            description="Query",
            query_text="SELECT * FROM users WHERE active=1",
        )
        result = build_pdf_buffer()
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")

    def test_build_pdf_buffer_with_project_documentation(self):
        """PDF com projeto que tem documentação Markdown."""
        p = Project.objects.create(
            name="ProjDoc",
            slug="proj-doc",
            short_description="Projeto com doc",
        )
        ProjectDocumentation.objects.create(
            project=p,
            title="Doc do Projeto",
            markdown_content="# Visão\n\n- Item 1\n- Item 2\n\n## Código\n\n```\ncode\n```",
        )
        result = build_pdf_buffer()
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")

    def test_build_pdf_buffer_with_resource_metadata(self):
        """PDF com recurso que tem detailed_description, repository_url, has_pentest, notes."""
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        Resource.objects.create(
            name="full-meta",
            slug="full-meta",
            resource_type=rt,
            short_description="Short",
            detailed_description="Detailed desc",
            repository_url="https://github.com/test/repo",
            has_pentest=True,
            notes="Some notes",
        )
        result = build_pdf_buffer()
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")

    def test_build_pdf_buffer_with_api_gateway(self):
        """PDF com recurso API Gateway e endpoints."""
        rt = ResourceType.objects.create(name="API Gateway", slug="api-gateway")
        r = Resource.objects.create(
            name="api-res",
            slug="api-res",
            resource_type=rt,
            short_description="API",
        )
        from arch_manager.apps.resources.models import (
            ApiGatewayEndpoint,
            ApiGatewayEndpointMethod,
        )

        ep = ApiGatewayEndpoint.objects.create(
            resource=r, path="/users", description="Users"
        )
        ApiGatewayEndpointMethod.objects.create(
            endpoint=ep, http_method="GET", description="List users"
        )
        result = build_pdf_buffer()
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")


class TestPdfExportHelpers:
    def test_format_json_valid(self):
        assert _format_json('{"a": 1}') == '{\n  "a": 1\n}'

    def test_format_json_invalid_returns_original(self):
        assert _format_json("not json") == "not json"

    def test_format_json_empty(self):
        assert _format_json("") == ""
        assert _format_json("   ") == ""

    def test_format_sql_adds_linebreaks(self):
        result = _format_sql("SELECT * FROM users WHERE id=1")
        assert "SELECT" in result
        assert "\n" in result or "FROM" in result

    def test_format_sql_empty(self):
        assert _format_sql("") == ""
        assert _format_sql("   ") == ""

    def test_break_long_lines_short_unchanged(self):
        short = "short line"
        assert _break_long_lines(short) == short

    def test_break_long_lines_long_breaks(self):
        long_line = "a" * 150
        result = _break_long_lines(long_line)
        assert "\n" in result
        assert all(len(part) <= 101 for part in result.split("\n"))
