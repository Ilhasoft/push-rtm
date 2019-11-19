# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from rest_framework_swagger.views import get_swagger_view

from django.conf.urls import url
from django.views.generic import RedirectView

from ureport.api.views import (
    OrgDetails,
    OrgList,
    PollDetails,
    PollList,
    DashboardDetails,
)

schema_view = get_swagger_view(title="API")


urlpatterns = [
    url(r"^$", RedirectView.as_view(pattern_name="api.v1.docs", permanent=False), name="api.v1"),
    url(r"^docs/", schema_view, name="api.v1.docs"),
    url(r"^orgs/$", OrgList.as_view(), name="api.v1.org_list"),
    url(r"^orgs/(?P<pk>[\w]+)/$", OrgDetails.as_view(), name="api.v1.org_details"),
    url(r"^polls/org/(?P<org>[\w]+)/$", PollList.as_view(), name="api.v1.org_poll_list"),
    url(r"^polls/(?P<pk>[\w]+)/$", PollDetails.as_view(), name="api.v1.poll_details"),
    url(r"^dashboard/(?P<pk>[\w]+)/$", DashboardDetails.as_view(), name="api.v1.dashboard_details"),
]
