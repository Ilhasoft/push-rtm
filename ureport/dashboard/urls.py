from django.conf.urls import url
from . import views


urlpatterns = [
    url(r"^local$", views.Dashboard.Local.as_view(), name="local"),
]
