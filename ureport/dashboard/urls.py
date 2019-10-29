from django.conf.urls import url
from .views import Dashboard


urlpatterns = [
    url(r"^local/$", Dashboard.Local.as_view(), name="dashboard.local"),
    url(r"^global/$", Dashboard.Global.as_view(), name="dashboard.global"),
]
