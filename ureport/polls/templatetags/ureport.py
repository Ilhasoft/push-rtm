# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import calendar

from urllib.parse import urlencode
from django import forms, template
from django.conf import settings
from django.template import TemplateSyntaxError
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.cache import cache
from django.utils.timesince import timesince

from ureport.utils import get_linked_orgs, json_date_to_datetime
from ureport.polls.models import Poll


register = template.Library()
logger = logging.getLogger(__name__)


@register.filter(name="add_placeholder")
def add_placeholder(field):
    field.field.widget.attrs["placeholder"] = field.label
    return field


@register.filter
def question_results(question):
    if not question:
        return None

    try:
        results = question.get_results()
        if results:
            return results[0]
    except Exception:
        if getattr(settings, "PROD", False):
            logger.error(
                "Question get results without segment in template tag raised exception", extra={"stack": True}
            )
        return None


@register.filter
def question_segmented_results(question, field):
    if not question:
        return None

    segment = None
    if field == "age":
        segment = dict(age="Age")
    elif field == "gender":
        segment = dict(gender="Gender")

    try:
        results = question.get_results(segment=segment)
        if results:
            return results
    except Exception:
        if getattr(settings, "PROD", False):
            logger.error("Question get results with segment in template tag raised exception", extra={"stack": True})
        return None


@register.filter
def get_range(value):
    return range(value)


@register.filter
def config(org, name):
    if not org:
        return None

    return org.get_config(name)


@register.filter
def org_arrow_link(org):
    if not org:
        return None

    if org.language in getattr(settings, "RTL_LANGUAGES", []):
        return mark_safe("&#8592;")

    return mark_safe("&#8594;")


@register.filter
def org_color(org, index):
    if not org:
        return None

    org_colors = org.get_config("common.colors")

    if org_colors:
        org_colors = org_colors.split(",")
    else:
        if org.get_config("common.primary_color") and org.get_config("common.secondary_color"):
            org_colors = [
                org.get_config("common.primary_color").strip(),
                org.get_config("common.secondary_color").strip(),
            ]
        else:
            org_colors = [
                getattr(settings, "UREPORT_DEFAULT_PRIMARY_COLOR"),
                getattr(settings, "UREPORT_DEFAULT_SECONDARY_COLOR"),
            ]

    return org_colors[int(index) % len(org_colors)].strip()


@register.filter
def transparency(color, alpha):
    if not color:
        return color

    if color[0] == "#":
        color = color[1:]

    if len(color) != 6:
        raise TemplateSyntaxError("add_transparency expect a long hexadecimal color, got: [%s]" % color)

    rgb_color = [int(c) for c in bytearray.fromhex(color)]
    rgb_color.append(alpha)

    return "rgba(%s, %s, %s, %s)" % tuple(rgb_color)


def lessblock(parser, token):
    args = token.split_contents()
    if len(args) != 1:
        raise TemplateSyntaxError("lessblock tag takes no arguments, got: [%s]" % ",".join(args))

    nodelist = parser.parse(("endlessblock",))
    parser.delete_first_token()
    return LessBlockNode(nodelist)


class LessBlockNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        style_output = '<style type="text/less" media="all">%s</style>' % output
        return style_output


# register our tag
lessblock = register.tag(lessblock)


@register.inclusion_tag("public/org_flags.html", takes_context=True)
def show_org_flags(context):
    request = context["request"]
    linked_orgs = get_linked_orgs(request.user.is_authenticated)
    return dict(
        linked_orgs=linked_orgs,
        break_pos=min(len(linked_orgs) / 2, 9),
        STATIC_URL=settings.STATIC_URL,
        is_iorg=context["is_iorg"],
    )


@register.inclusion_tag("v2/public/edit_content.html", takes_context=True)
def edit_content(context, reverse_name, reverse_arg=None, anchor_id="", extra_css_classes="", icon_color="dark"):
    request = context["request"]

    url_args = []
    if reverse_arg:
        url_args.append(reverse_arg)

    edit_url = f"{reverse(reverse_name, args=url_args)}{anchor_id}"

    return dict(
        request=request,
        edit_url=edit_url,
        extra_css_classes=extra_css_classes,
        icon_color=icon_color,
        STATIC_URL=settings.STATIC_URL,
    )


@register.simple_tag(takes_context=True)
def org_host_link(context):
    request = context["request"]
    try:
        org = request.org
        return org.build_host_link(True)
    except Exception:
        return "https://%s" % getattr(settings, "HOSTNAME", "localhost")


@register.filter
def is_select(field):
    return isinstance(field.field.widget, forms.Select)


@register.filter
def is_multiple_select(field):
    return isinstance(field.field.widget, forms.SelectMultiple)


@register.filter
def is_textarea(field):
    return isinstance(field.field.widget, forms.Textarea)


@register.filter
def is_input(field):
    return isinstance(
        field.field.widget, (forms.TextInput, forms.NumberInput, forms.EmailInput, forms.PasswordInput, forms.URLInput)
    )


@register.filter
def is_checkbox(field):
    return isinstance(field.field.widget, forms.CheckboxInput)


@register.filter
def is_multiple_checkbox(field):
    return isinstance(field.field.widget, forms.CheckboxSelectMultiple)


@register.filter
def is_radio(field):
    return isinstance(field.field.widget, forms.RadioSelect)


@register.filter
def is_file(field):
    return isinstance(field.field.widget, forms.FileInput)


# Based on https://github.com/webstack/webstack-django-sorting


@register.tag(name="autosort")
def autosort(parser, token):
    bits = [b for b in token.split_contents()]

    if len(bits) < 2:
        raise template.TemplateSyntaxError("anchor tag takes at least 1 argument.")

    try:
        title = _(bits[2][3:-2])
    except IndexError:
        title = bits[1].capitalize()

    try:
        only_url = bits[3]
    except IndexError:
        only_url = False

    return SortAnchorNode(bits[1].strip(), title.strip(), bool(only_url))


class SortAnchorNode(template.Node):

    sort_directions = {
        "asc": {"icon": "up-arrow", "inverse": "desc"},
        "desc": {"icon": "down-arrow", "inverse": "asc"},
        "": {"icon": "", "inverse": "asc"},
    }

    def __init__(self, field, title, only_url=False):
        self.field = field
        self.title = title
        self.only_url = only_url

    def render(self, context):
        request = context["request"]
        getvars = request.GET.copy()

        if "sort" in getvars:
            sortby = getvars["sort"]
            del getvars["sort"]
        else:
            sortby = ""

        if "dir" in getvars:
            sortdir = self.sort_directions.get(getvars["dir"], self.sort_directions[""])
            del getvars["dir"]
        else:
            sortdir = self.sort_directions[""]

        if sortby == self.field:
            getvars["dir"] = sortdir["inverse"]
            icon = sortdir["icon"]
        else:
            getvars["dir"] = "desc"
            icon = "up-arrow"

        if len(getvars.keys()) > 0:
            urlappend = "&{}".format(getvars.urlencode())
        else:
            urlappend = ""

        if icon:
            icon = static("svg/{}.svg".format(icon))
            title = '{} <img src="{}">'.format(self.title, icon)
        else:
            title = self.title

        if "dir" in getvars:
            url = "{}?sort={}{}".format(request.path, self.field, urlappend)
        else:
            url = "{}{}{}".format(request.path, "?" if urlappend else "", urlappend)

        if self.only_url:
            return url

        return '<a href="{}" title="{}">{}</a>'.format(url, self.title, title)


@register.filter(name="user_org_group")
def user_org_group(user, org):
    if org in user.org_admins.all():
        return "UNCT Admin"

    if org in user.org_editors.all():
        return "UNCT Editor"

    if org in user.org_viewers.all():
        return "UNCT Viewer"


@register.filter(name="items_to_list")
def items_to_list(items_list):
    return list(map(lambda x: int(x), items_list))


@register.filter(name="get_language")
def get_language(language):
    if language and language != "base":
        import pycountry

        return pycountry.languages.get(alpha_3=language).name
    return None


@register.filter(name="get_value_in_qs")
def get_value_in_qs(queryset, key):
    sdgs = []
    for a in queryset.values_list(key, flat=True):
        [sdgs.append(b) for b in a]

    sdgs = list(set(sdgs))
    sdgs.sort()
    return sdgs


@register.filter(name="get_sdg")
def get_sdg(key):
    return dict(settings.SDG_LIST).get(key)


@register.filter(name="get_poll_sync_status")
def get_poll_sync_status(obj):
    if obj.has_synced:
        last_synced = cache.get(Poll.POLL_RESULTS_LAST_SYNC_TIME_CACHE_KEY % (obj.org.pk, obj.flow_uuid), None)
        if last_synced:
            return timesince(json_date_to_datetime(last_synced))

        # we know we synced do not check the the progress since that is slow
        return "Synced 100%"

    sync_progress = obj.get_sync_progress()
    return "Syncing... {0:.1f}%".format(sync_progress)


@register.filter(name="get_month_name")
def get_month_name(index):
    return calendar.month_name[index]


@register.simple_tag
def urlparams(*_, **kwargs):
    safe_args = {k: v for k, v, in kwargs.items() if v is not None}
    if safe_args:
        return "?{}".format(urlencode(safe_args))
    return ""


@register.filter(name="get_group_name")
def get_group_name(name):
    return {"Administrators": "UNCT Admin", "Editors": "UNCT Editor", "Viewers": "UNCT Viewer"}.get(name)


@register.simple_tag
def check_permissions(org, user):
    if user.is_authenticated:
        if user.is_superuser or user.groups.filter(name="Global Viewers"):
            return True
        elif org and org in user.get_user_orgs():
            return True
    return False


@register.filter(name="only_is_active")
def only_is_active(queryset):
    return queryset.filter(is_active=True)


@register.filter(name="is_admin_user")
def is_admin_user(user):
    if user.groups.filter(name="Administrators"):
        return True
    return False


@register.filter(name="get_org_url")
def get_org_url(org):
    return settings.SITE_HOST_PATTERN.format(org.subdomain)
