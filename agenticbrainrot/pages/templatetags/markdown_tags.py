import markdown as md
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="render_markdown")
def render_markdown(value):
    """Render a markdown string to HTML."""
    if not value:
        return ""
    html = md.markdown(value, extensions=["extra", "codehilite", "nl2br"])
    return mark_safe(html)  # noqa: S308
