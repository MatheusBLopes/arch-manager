import pytest
from django.urls import reverse

from arch_manager.apps.resources.models import Resource, ResourceType

from .models import ResourceDocumentation


@pytest.fixture
def resource_with_doc(db):
    rt = ResourceType.objects.create(name="Lambda", slug="lambda")
    r = Resource.objects.create(
        name="test-resource",
        slug="test-resource",
        resource_type=rt,
        short_description="Recurso de teste",
    )
    doc = ResourceDocumentation.objects.create(
        resource=r,
        title="Doc do recurso",
        markdown_content="# Título\n\nConteúdo em **markdown**.",
    )
    return r, doc


@pytest.mark.django_db
class TestResourceDocumentationModel:
    def test_create_documentation(self):
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        r = Resource.objects.create(
            name="r",
            slug="r",
            resource_type=rt,
            short_description="x",
        )
        doc = ResourceDocumentation.objects.create(
            resource=r,
            title="Doc",
            markdown_content="# Hello",
        )
        assert doc.resource == r
        assert "Doc" in str(doc)


@pytest.mark.django_db
class TestDocumentationViews:
    def test_documentation_edit_get(self, client, resource_with_doc):
        r, _ = resource_with_doc
        response = client.get(
            reverse("docs:edit", kwargs={"resource_slug": r.slug})
        )
        assert response.status_code == 200

    def test_documentation_edit_get_resource_without_doc(self, client):
        """Testa o branch quando recurso não tem documentação (initial title)."""
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        r = Resource.objects.create(
            name="no-doc",
            slug="no-doc",
            resource_type=rt,
            short_description="Sem doc",
        )
        response = client.get(
            reverse("docs:edit", kwargs={"resource_slug": r.slug})
        )
        assert response.status_code == 200

    def test_documentation_edit_post_create(self, client):
        """Cria documentação para recurso que não tinha."""
        rt = ResourceType.objects.create(name="Lambda", slug="lambda")
        r = Resource.objects.create(
            name="new-doc",
            slug="new-doc",
            resource_type=rt,
            short_description="X",
        )
        response = client.post(
            reverse("docs:edit", kwargs={"resource_slug": r.slug}),
            {
                "title": "Doc nova",
                "markdown_content": "# Conteúdo",
            },
        )
        assert response.status_code == 302
        assert ResourceDocumentation.objects.filter(resource=r).exists()

    def test_documentation_edit_post(self, client, resource_with_doc):
        r, doc = resource_with_doc
        response = client.post(
            reverse("docs:edit", kwargs={"resource_slug": r.slug}),
            {
                "title": "Doc atualizada",
                "markdown_content": "## Novo conteúdo\n\nMarkdown **ok**.",
            },
        )
        assert response.status_code == 302
        doc.refresh_from_db()
        assert "Novo conteúdo" in doc.markdown_content


@pytest.mark.django_db
class TestDocumentationForms:
    def test_documentation_form_accepts_markdown(self):
        from .forms import ResourceDocumentationForm

        form = ResourceDocumentationForm(
            data={
                "title": "Test Doc",
                "markdown_content": "# Heading\n\n- item 1\n- item 2",
            }
        )
        assert form.is_valid()

    def test_documentation_form_accepts_empty_markdown(self):
        from .forms import ResourceDocumentationForm

        form = ResourceDocumentationForm(
            data={
                "title": "Test Doc",
                "markdown_content": "",
            }
        )
        assert form.is_valid()


@pytest.mark.django_db
class TestDocsViewsRenderMarkdown:
    def test_render_markdown_empty(self):
        from .views import render_markdown

        assert render_markdown("") == ""
        assert render_markdown(None) == ""

    def test_render_markdown_content(self):
        from .views import render_markdown

        result = render_markdown("# Hello")
        assert "Hello" in result
        assert "<h1" in result


@pytest.mark.django_db
class TestDocsExtrasTemplateTag:
    def test_markdown_render_empty_returns_empty(self):
        """Cobre o branch 'if not text' do filtro markdown_render."""
        from arch_manager.apps.docs.templatetags.docs_extras import markdown_render

        assert markdown_render("") == ""
        assert markdown_render(None) == ""
