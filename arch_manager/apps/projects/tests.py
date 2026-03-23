import pytest
from django.urls import reverse

from .forms import ProjectForm, ProjectDocumentationForm
from .models import Project, ProjectDocumentation


@pytest.mark.django_db
class TestProjectModel:
    def test_create_project(self):
        p = Project.objects.create(
            name="Checkout",
            slug="checkout",
            short_description="Sistema de checkout",
        )
        assert p.name == "Checkout"
        assert str(p) == "Checkout"

    def test_project_str(self):
        p = Project.objects.create(name="API", slug="api", short_description="API")
        assert "API" in str(p)


@pytest.mark.django_db
class TestProjectDocumentationModel:
    def test_create_project_documentation(self):
        p = Project.objects.create(name="P", slug="p", short_description="X")
        doc = ProjectDocumentation.objects.create(
            project=p,
            title="Doc",
            markdown_content="# Hello",
        )
        assert doc.project == p
        assert "P" in str(doc) or "Doc" in str(doc)


@pytest.mark.django_db
class TestProjectForm:
    def test_project_form_valid_auto_slug(self):
        form = ProjectForm(
            data={
                "name": "Novo Projeto",
                "short_description": "Descrição do projeto",
            }
        )
        assert form.is_valid()
        project = form.save()
        assert project.slug == "novo-projeto"
        assert project.name == "Novo Projeto"

    def test_project_form_unique_slug_on_duplicate(self):
        Project.objects.create(name="Test", slug="test", short_description="X")
        form = ProjectForm(
            data={
                "name": "Test",
                "short_description": "Outro projeto",
            }
        )
        assert form.is_valid()
        project = form.save()
        assert project.slug.startswith("test-")
        assert project.slug != "test"

    def test_project_form_unique_slug_multiple_collisions(self):
        """Exercita o loop de slug quando test e test-1 já existem."""
        Project.objects.create(name="Test", slug="test", short_description="X")
        Project.objects.create(name="Test", slug="test-1", short_description="X")
        form = ProjectForm(
            data={
                "name": "Test",
                "short_description": "Terceiro",
            }
        )
        assert form.is_valid()
        project = form.save()
        assert project.slug == "test-2"

    def test_project_form_update_excludes_self_from_slug_check(self):
        p = Project.objects.create(name="Original", slug="original", short_description="X")
        form = ProjectForm(
            data={
                "name": "Original",
                "short_description": "Nova desc",
            },
            instance=p,
        )
        assert form.is_valid()
        project = form.save()
        assert project.slug == "original"


@pytest.mark.django_db
class TestProjectDocumentationForm:
    def test_project_documentation_form_valid(self):
        form = ProjectDocumentationForm(
            data={
                "title": "Doc do Projeto",
                "markdown_content": "# Visão Geral\n\nConteúdo.",
            }
        )
        assert form.is_valid()


@pytest.mark.django_db
class TestProjectViews:
    def test_project_list_responds_200(self, client):
        response = client.get(reverse("projects:list"))
        assert response.status_code == 200

    def test_project_create_get(self, client):
        response = client.get(reverse("projects:create"))
        assert response.status_code == 200

    def test_project_create_post(self, client):
        response = client.post(
            reverse("projects:create"),
            {
                "name": "Meu Projeto",
                "short_description": "Descrição do projeto",
            },
        )
        assert response.status_code == 302
        assert Project.objects.filter(slug="meu-projeto").exists()

    def test_project_detail_responds_200(self, client):
        p = Project.objects.create(name="P", slug="p", short_description="X")
        response = client.get(reverse("projects:detail", kwargs={"slug": p.slug}))
        assert response.status_code == 200

    def test_project_update_get(self, client):
        p = Project.objects.create(name="P", slug="p", short_description="X")
        response = client.get(reverse("projects:update", kwargs={"slug": p.slug}))
        assert response.status_code == 200

    def test_project_update_post(self, client):
        p = Project.objects.create(name="P", slug="p", short_description="X")
        response = client.post(
            reverse("projects:update", kwargs={"slug": p.slug}),
            {"name": "P Atualizado", "short_description": "Nova desc"},
        )
        assert response.status_code == 302
        p.refresh_from_db()
        assert p.name == "P Atualizado"

    def test_project_delete_post(self, client):
        p = Project.objects.create(name="P", slug="p", short_description="X")
        response = client.post(reverse("projects:delete", kwargs={"slug": p.slug}))
        assert response.status_code == 302
        assert not Project.objects.filter(pk=p.pk).exists()

    def test_project_delete_get_redirects(self, client):
        p = Project.objects.create(name="P", slug="p", short_description="X")
        response = client.get(reverse("projects:delete", kwargs={"slug": p.slug}))
        assert response.status_code == 302

    def test_project_docs_edit_get_without_doc(self, client):
        p = Project.objects.create(name="P", slug="p", short_description="X")
        response = client.get(reverse("projects:docs-edit", kwargs={"slug": p.slug}))
        assert response.status_code == 200

    def test_project_docs_edit_get_with_doc(self, client):
        p = Project.objects.create(name="P", slug="p", short_description="X")
        ProjectDocumentation.objects.create(
            project=p, title="Doc", markdown_content="# Hi"
        )
        response = client.get(reverse("projects:docs-edit", kwargs={"slug": p.slug}))
        assert response.status_code == 200

    def test_project_docs_edit_post_create(self, client):
        p = Project.objects.create(name="P", slug="p", short_description="X")
        response = client.post(
            reverse("projects:docs-edit", kwargs={"slug": p.slug}),
            {"title": "Doc Nova", "markdown_content": "# Conteúdo"},
        )
        assert response.status_code == 302
        assert ProjectDocumentation.objects.filter(project=p).exists()

    def test_project_docs_edit_post_update(self, client):
        p = Project.objects.create(name="P", slug="p", short_description="X")
        doc = ProjectDocumentation.objects.create(
            project=p, title="Doc", markdown_content="# Old"
        )
        response = client.post(
            reverse("projects:docs-edit", kwargs={"slug": p.slug}),
            {"title": "Doc Atualizada", "markdown_content": "# Novo conteúdo"},
        )
        assert response.status_code == 302
        doc.refresh_from_db()
        assert "Novo" in doc.markdown_content
