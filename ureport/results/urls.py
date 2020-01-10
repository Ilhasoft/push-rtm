from django.conf.urls import url

from .views import PollReadView, PollQuestionResultsView, PollGlobalReadView, PollGlobalDataView


urlpatterns = [
    url(r"^survey/(?P<pk>[0-9]+)/$", PollReadView.as_view(), name="results.poll_read"),
    url(r"^survey/(?P<pk>\d+)/pollquestion/$", PollQuestionResultsView.as_view(), {}, "results.pollquestion_results"),
    url(r'^survey-global/(?P<pk>[0-9]+)/$', PollGlobalReadView.as_view(), name="results.global_poll_read"),
    url(r'^survey-global/(?P<pk>[0-9]+)/data/(?P<unct>[0-9]+)/$', PollGlobalDataView.as_view(), name="results.global_poll_data"),
]
