import json
import random

from django.conf import settings

from smartmin.views import SmartTemplateView

from ureport.polls.models import PollQuestion


class Dashboard:
    @classmethod
    def get_bubble_chart_data_sdgs_being_tracked(self, questions, mock=False):
        '''
        return data to chart.js bubble chart.
        get questions queryset and boolean mock parammeter.
        default mock is False.
        '''
        tracked_sdg = []
        not_tracked_sdg = []
        datasets = []

        #  USE DATA MOCK
        if mock is True:
            for key, value in settings.SDG_LIST:
                if key % 2 == 0:
                    tracked_sdg.append(settings.SDG_LIST[key])
                    values = [random.randint(7, 70) for n in range(4)]

                    datasets.append(
                        {
                            'label': '{} {}'.format(key, value),
                            'data': [{"x": values[0], "y": values[1], "r": values[2]}],
                            'backgroundColor': settings.SDG_COLOR.get(key),
                            'borderColor': '#FFFFFF',
                        }
                    )
                else:
                    not_tracked_sdg.append(settings.SDG_LIST[key-1])

        else:  # USE REAL DATA
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
                    tracked_sdg.append(settings.SDG_LIST[key-1])
                else:
                    not_tracked_sdg.append(settings.SDG_LIST[key-1])

            # implement chart.js bubblechart data.datasets model for all SDGs
            for key, value in tuple(tracked_sdg):
                sdg_with_data = sdgs_with_data.get(key)

                datasets.append(
                    {
                        'label': '{} {}'.format(key, value),
                        'data': [
                            {
                                "x": sdg_with_data.get("total_responded", 0),
                                "y": len(sdg_with_data.get("questions", [])),
                                "r": sdg_with_data.get("percentage_in_questions", 0),
                            }
                        ],
                        'backgroundColor': settings.SDG_COLOR.get(key),
                        'borderColor': '#FFFFFF',
                    }
                )

        data = {
            'tracked_sdgs': tuple(tracked_sdg),
            'not_tracked_sdgs': tuple(not_tracked_sdg),
            'datasets': datasets,
        }

        return data

    class Local(SmartTemplateView):
        template_name = "dashboard/local.html"

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            questions = PollQuestion.objects.filter(is_active=True, poll__org=self.request.org, poll__is_active=True)
            context["sdgs_bublle_data"] = Dashboard.get_bubble_chart_data_sdgs_being_tracked(questions)

            return context

    class Global(SmartTemplateView):
        template_name = "dashboard/global.html"
