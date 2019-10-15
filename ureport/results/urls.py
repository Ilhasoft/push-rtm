from django.conf.urls import url

from .views import PollReadView, PollQuestionResultsView

urlpatterns = [
    url(r"^survey/(?P<pk>[0-9]+)/$", PollReadView.as_view(), name="results.poll_read"),
    url(r"^survey/(?P<pk>\d+)/pollquestion/$", PollQuestionResultsView.as_view(), {}, "results.pollquestion_results"),
]
