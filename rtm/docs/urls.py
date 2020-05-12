from django.conf.urls import url
from django.views.generic import TemplateView

urlpatterns = [
    url(r"^$", TemplateView.as_view(template_name="docs/login.html"), name="docs.login"),
    url(r"^uncts-users/$", TemplateView.as_view(template_name="docs/uncts_users.html"), name="docs.uncts_users"),
    url(
        r"^uncts-repository/$",
        TemplateView.as_view(template_name="docs/uncts_repository.html"),
        name="docs.uncts_repository",
    ),
    url(r"^uncts-surveys/$", TemplateView.as_view(template_name="docs/uncts_surveys.html"), name="docs.uncts_surveys"),
    url(
        r"^uncts-dashboard/$",
        TemplateView.as_view(template_name="docs/uncts_dashboard.html"),
        name="docs.uncts_dashboard",
    ),
    url(r"^global-uncts/$", TemplateView.as_view(template_name="docs/global_uncts.html"), name="docs.global_uncts"),
    url(r"^global-users/$", TemplateView.as_view(template_name="docs/global_users.html"), name="docs.global_users"),
    url(
        r"^global-repository/$",
        TemplateView.as_view(template_name="docs/global_repository.html"),
        name="docs.global_repository",
    ),
    url(
        r"^global-surveys/$",
        TemplateView.as_view(template_name="docs/global_surveys.html"),
        name="docs.global_surveys",
    ),
    url(
        r"^global-dashboard/$",
        TemplateView.as_view(template_name="docs/global_dashboard.html"),
        name="docs.global_dashboard",
    ),
]
