from smartmin.views import SmartTemplateView


class ResultPollView(SmartTemplateView):
    template_name = "results/poll_result.html"
    permission = "polls.poll_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
