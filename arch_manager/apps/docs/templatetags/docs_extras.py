import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def markdown_render(text):
    """Renderiza conteúdo Markdown para HTML."""
    if not text:
        return ""
    html = markdown.markdown(
        text,
        extensions=["extra", "codehilite", "toc"],
        extension_configs={
            "codehilite": {"css_class": "highlight"},
        },
    )
    return mark_safe(html)
