from django import template

register = template.Library()


@register.filter(name="format_to_percent")
def format_to_percent(field):
    return str(int(field)) + "%" if field is not None else ""
