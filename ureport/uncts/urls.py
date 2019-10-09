from django.conf.urls import url

from .views import CreateView, ListView, EditView

urlpatterns = [
    url(r"^$", ListView.as_view(), name="uncts.unct_list"),
    url(r"^create/", CreateView.as_view(), name="uncts.unct_create"),
    url(r"^(?P<unct>[0-9]+)/edit$", EditView.as_view(), name="uncts.unct_update"),
]
