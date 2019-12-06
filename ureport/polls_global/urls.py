from django.conf.urls import url

from .views import ListView, CreateView, EditView

urlpatterns = [
    url(r"^$", ListView.as_view(), name="polls_global.poll_list"),
    url(r"^create/", CreateView.as_view(), name="polls_global.poll_create"),
    url(r"^(?P<poll>[0-9]+)/edit$", EditView.as_view(), name="polls_global.poll_update"),
]
