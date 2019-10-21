from django.conf.urls import url
from . import views


urlpatterns = [
    url(r"^local/$", views.Dashboard.Local.as_view(), name="dashboard.local"),
    url(r"^global/$", views.Dashboard.Global.as_view(), name="dashboard.global"),
]
