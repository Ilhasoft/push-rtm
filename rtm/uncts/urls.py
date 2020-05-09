from django.conf.urls import url

from .views import CreateView, ListView, EditView, RedirectToUNCTView

urlpatterns = [
    url(r"^$", ListView.as_view(), name="uncts.unct_list"),
    url(r"^create/", CreateView.as_view(), name="uncts.unct_create"),
    url(r"^(?P<unct>[0-9]+)/edit$", EditView.as_view(), name="uncts.unct_update"),
    url(r"^redirect/$", RedirectToUNCTView.as_view(), name="uncts.redirect"),
    url(r"^redirect/(?P<subdomain>\w+)/$", RedirectToUNCTView.as_view(), name="uncts.redirect"),
]
