from django.conf.urls import url
from . import views


urlpatterns = [
    #url(r"^local/$", views.Local.as_view(), name="dashboard.local"),
    #url(r"^global/$", views.Global.as_view(), name="dashboard.global"),
    url(r"^$", views.Dashboard.as_view(), name="dashboard"),
]
