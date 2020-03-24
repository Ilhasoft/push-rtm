from django.conf.urls import url

from .views import ListView, CreateView, EditView, GrantView, GrantUpdateView

urlpatterns = [
    url(r"^$", ListView.as_view(), name="polls_global.poll_list"),
    url(r"^create/", CreateView.as_view(), name="polls_global.poll_create"),
    url(r"^(?P<poll>[0-9]+)/edit$", EditView.as_view(), name="polls_global.poll_update"),
    url(r"^(?P<poll>[0-9]+)/grant/", GrantView.as_view(), name="polls_global.poll_grant"),
    url(r"^(?P<poll>[0-9]+)/update/(?P<survey>[0-9]+)", GrantUpdateView.as_view(), name="polls_global.poll_update"),
]
