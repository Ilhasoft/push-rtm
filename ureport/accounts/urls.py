from django.conf.urls import url

from .views import ListView, CreateView, EditView, DeleteView


urlpatterns = [
    url(r"^$", ListView.as_view(), name="accounts.user_list"),
    url(r"^create/", CreateView.as_view(), name="accounts.user_create"),
    url(r"^(?P<user>[0-9]+)/update/$", EditView.as_view(), name="accounts.user_update"),
    url(r"^(?P<user>[0-9]+)/delete/$", DeleteView.as_view(), name="accounts.user_delete"),
    url(r"^(?P<org>[0-9]+)$", ListView.as_view(), name="accounts.user_org_list"),
    url(r"^(?P<org>[0-9]+)/create/", CreateView.as_view(), name="accounts.user_org_create"),
    url(r"^(?P<org>[0-9]+)/(?P<user>[0-9]+)/update/$", EditView.as_view(), name="accounts.user_org_update"),
    url(r"^(?P<org>[0-9]+)/(?P<user>[0-9]+)/delete/$", DeleteView.as_view(), name="accounts.user_org_delete"),
]
