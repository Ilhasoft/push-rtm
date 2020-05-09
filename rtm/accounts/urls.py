from django.conf.urls import url

from .views import (
    ListView,
    EditView,
    DeleteView,
    GlobalListView,
    GlobalEditView,
    GlobalDeleteView,
    ActivateView,
    GlobalActivateView,
)

urlpatterns = [
    url(r"^$", ListView.as_view(), name="accounts.user_list"),
    url(r"^(?P<user>[0-9]+)/update/$", EditView.as_view(), name="accounts.user_update"),
    url(r"^(?P<user>[0-9]+)/delete/$", DeleteView.as_view(), name="accounts.user_delete"),
    url(r"^(?P<org>[0-9]+)$", ListView.as_view(), name="accounts.user_org_list"),
    url(r"^(?P<org>[0-9]+)/(?P<user>[0-9]+)/update/$", EditView.as_view(), name="accounts.user_org_update"),
    url(r"^(?P<org>[0-9]+)/(?P<user>[0-9]+)/delete/$", DeleteView.as_view(), name="accounts.user_org_delete"),
    url(r"^(?P<org>[0-9]+)/(?P<user>[0-9]+)/activate/$", ActivateView.as_view(), name="accounts.user_org_activate"),
    # global admin
    url(r"^global/(?P<user>[0-9]+)/update/$", GlobalEditView.as_view(), name="accounts.global_user_update"),
    url(r"^global/$", GlobalListView.as_view(), name="accounts.global_list"),
    url(r"^global/(?P<user>[0-9]+)/delete/$", GlobalDeleteView.as_view(), name="accounts.global_user_delete"),
    url(r"^global/(?P<user>[0-9]+)/activate/$", GlobalActivateView.as_view(), name="accounts.global_user_activate"),
]
