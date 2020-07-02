# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views import static
from django.views.generic import TemplateView


admin.autodiscover()


urlpatterns = [
    url(r"^", include("rtm.dashboard.urls")),
    url(r"^api/", include("rtm.api.urls")),
    url(r"^users/", include("dash.users.urls")),
    url(r"^users/", include("rtm.accounts.urls")),
    url(r"^uncts/", include("rtm.uncts.urls")),
    url(r"^surveys/", include("rtm.polls.urls")),
    url(r"^results/", include("rtm.results.urls")),
    url(r"^authentication/", include("rtm.authentication.urls")),
    url(r"^surveys-global/", include("rtm.polls_global.urls")),
    url(r"^blocked/", TemplateView.as_view(template_name="blocked_user.html"), name="blocked"),
]

if settings.DEBUG:

    try:
        import debug_toolbar

        urlpatterns.append(url(r"^__debug__/", include(debug_toolbar.urls)))
    except ImportError:
        pass

    urlpatterns = [
        url(r"^media/(?P<path>.*)$", static.serve, {"document_root": settings.MEDIA_ROOT, "show_indexes": True}),
        url(r"", include("django.contrib.staticfiles.urls")),
    ] + urlpatterns
