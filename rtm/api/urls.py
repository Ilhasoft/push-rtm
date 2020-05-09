from django.conf.urls import url
from django.views.generic import RedirectView

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from rtm.api.views import OrgDetails, OrgList, PollDetails, PollList, DashboardDetails


schema_view = get_schema_view(
    openapi.Info(title="RTM API", default_version="v1", description="Real Time Monitor",),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    url(r"^$", RedirectView.as_view(pattern_name="api.v1.docs", permanent=False), name="api.v1"),
    url(r"^schema(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="api.v1.schema"),
    url(r"^docs/$", schema_view.with_ui("swagger", cache_timeout=0), name="api.v1.docs"),
    url(r"^orgs/$", OrgList.as_view(), name="api.v1.org_list"),
    url(r"^orgs/(?P<pk>[\w]+)/$", OrgDetails.as_view(), name="api.v1.org_details"),
    url(r"^polls/org/(?P<org>[\w]+)/$", PollList.as_view(), name="api.v1.org_poll_list"),
    url(r"^polls/(?P<pk>[\w]+)/$", PollDetails.as_view(), name="api.v1.poll_details"),
    url(r"^dashboard/(?P<pk>[\w]+)/$", DashboardDetails.as_view(), name="api.v1.dashboard_details"),
]
