from django import template

register = template.Library()


@register.filter(name="is_global_viewer_active")
def is_global_viewer_active(user):
    group = user.groups.filter(name="Global Viewers")
    return True if group else False
