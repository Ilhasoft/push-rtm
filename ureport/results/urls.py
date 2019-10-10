from django.conf.urls import url

from .views import ResultPollView

urlpatterns = [
    url(r"^survey/(?P<pk>[0-9]+)/$", ResultPollView.as_view(), name="results.poll_read"),
]
