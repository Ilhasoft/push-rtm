from django.conf.urls import url
from .views import Dashboard, DashboardDataView


urlpatterns = [
    url(r"^$", Dashboard.as_view(), name="dashboard"),
    url(r"dashboard/data/", DashboardDataView.as_view(), name="dashboard_data"),
]
