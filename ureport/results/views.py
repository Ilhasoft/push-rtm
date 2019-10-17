import json

from django.http import HttpResponse
from django.conf import settings

from smartmin.views import SmartReadView

from ureport.polls.models import Poll, PollQuestion


class PollReadView(SmartReadView):
    template_name = "results/poll_result.html"
    permission = "polls.poll_list"
    model = Poll

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["org"] = self.request.org
        context["poll"] = self.get_object()
        context["sdgs"] = settings.SDG_LIST
        return context

    def derive_queryset(self):
        queryset = super(PollReadView, self).derive_queryset()
        queryset = queryset.filter(org=self.request.org, is_active=True, has_synced=True)
        return queryset


class PollQuestionResultsView(SmartReadView):
    model = PollQuestion

    def derive_queryset(self):
        queryset = super(PollQuestionResultsView, self).derive_queryset()
        queryset = queryset.filter(poll__org=self.request.org, is_active=True)
        return queryset

    def render_to_response(self, context, **kwargs):
        segment = self.request.GET.get("segment", None)
        if segment:
            segment = json.loads(segment)

        results = self.object.get_results(segment=segment)

        return HttpResponse(json.dumps(results))
