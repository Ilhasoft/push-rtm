from django.conf.urls import url

from .views import ListView

urlpatterns = [
    url(r"^$", ListView.as_view(), name="worldmap.map_list"),
]
