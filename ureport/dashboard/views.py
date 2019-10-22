import json

from django.conf import settings

from smartmin.views import SmartTemplateView

from ureport.polls.models import PollQuestion


class Dashboard:
    class Local(SmartTemplateView):
        template_name = "dashboard/local.html"

        def get_bubble_chart_data_mock(self):
            """
            for test in templates
            """
            import random

            fake_data = {}
            for i in range(17):
                values = [random.randint(7, 70) for n in range(4)]
                fake_data["bubble-sdg-{}".format(i+1)] = {"x": values[0], "y": values[1], "r": values[2]}
            return fake_data

        def get_bubble_chart_data(self, questions):

            # create dict with sdgs and yours questions. eg: {1: {'questions': []}}
            sdgs_with_data = {
                sdg[0]: {"questions": [q for q in questions if sdg[0] in q.sdgs]}
                for sdg in settings.SDG_LIST
            }

            # add keys total_responded and percentage_in_questions to sdgs_with_data
            for key, value in sdgs_with_data.items():
                if len(value["questions"]) > 0:
                    sdgs_with_data[key]["total_responded"] = value["questions"][
                        0
                    ].get_responded()
                    sdgs_with_data[key]["percentage_in_questions"] = (
                        len(value["questions"]) / questions.count()
                    ) * 100  # (part / total) * 100

            # implement chart.js bubble chart data model for all SDGs
            data = {}

            for key, value in settings.SDG_LIST:
                sdg_with_data = sdgs_with_data.get(key)

                data["bubble-sdg-{}".format(key)] = {
                    "x": sdg_with_data.get("total_responded", 0),
                    "y": len(sdg_with_data.get("questions", [])),
                    "r": sdg_with_data.get("percentage_in_questions", 0),
                }
            
            # for use data mock uncommented below line
            # data = self.get_bubble_chart_data_mock()

            return data

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            questions = PollQuestion.objects.filter(is_active=True, poll__org=self.request.org, poll__is_active=True)
            context["bublle_data"] = self.get_bubble_chart_data(questions)

            return context

    class Global(SmartTemplateView):
        template_name = "dashboard/global.html"
