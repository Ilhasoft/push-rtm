import json
import random
import datetime

from django.conf import settings

from smartmin.views import SmartTemplateView

from ureport.polls.models import PollQuestion


class Dashboard:
    @classmethod
    def get_sdgs_tracked_bubble_chart_data(self, questions, mock=False):
        """
        return data to chart.js bubble chart.
        get questions queryset and boolean mock parammeter.
        default mock is False.
        """
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
                            "label": "{} {}".format(key, value),
                            "data": [{"x": values[0], "y": values[1], "r": values[2]}],
                            "backgroundColor": settings.SDG_COLOR.get(key),
                            "borderColor": "#FFFFFF",
                        }
                    )
                else:
                    not_tracked_sdg.append(settings.SDG_LIST[key - 1])

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
                    sdgs_with_data[key]["percentage_in_questions"] = int(
                        (len(value["questions"]) / questions.count()) * 100
                    )  # (part / total) * 100
                    tracked_sdg.append(settings.SDG_LIST[key - 1])
                else:
                    not_tracked_sdg.append(settings.SDG_LIST[key - 1])

            # implement chart.js bubblechart data.datasets model for all SDGs
            for key, value in tuple(tracked_sdg):
                sdg_with_data = sdgs_with_data.get(key)

                datasets.append(
                    {
                        "label": "{} {}".format(key, value),
                        "data": [
                            {
                                "x": sdg_with_data.get("total_responded", 0),
                                "y": len(sdg_with_data.get("questions", [])),
                                "r": sdg_with_data.get("percentage_in_questions", 0),
                            }
                        ],
                        "backgroundColor": settings.SDG_COLOR.get(key),
                        "borderColor": "#FFFFFF",
                    }
                )

        data = {
            "tracked_sdgs": tuple(tracked_sdg),
            "not_tracked_sdgs": tuple(not_tracked_sdg),
            "datasets": datasets,
        }

        return data

    @classmethod
    def questions_filter(self, questions, sorted_field):
        one_year_ago = datetime.date.today() - datetime.timedelta(days=365)
        one_moth_ago = datetime.date.today() - datetime.timedelta(days=30)
        one_week_ago = datetime.date.today() - datetime.timedelta(days=7)

        filters = {}

        if sorted_field is None:
            filters["created_on__gte"] = one_year_ago
        elif sorted_field == "sdg_track_last_month":
            filters["created_on__gte"] = one_moth_ago
        elif sorted_field == "sdg_track_last_week":
            filters["created_on__gte"] = one_week_ago

        questions = questions.filter(**filters)

        return questions

    class Local(SmartTemplateView):
        template_name = "dashboard/local.html"

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            sorted_field = self.request.GET.get("sort")

            questions = PollQuestion.objects.filter(
                is_active=True, poll__org=self.request.org, poll__is_active=True
            )

            ### SDG TRAKED BUBBLE CHART ###
            sdg_tracked_questions = PollQuestion.objects.filter(
                is_active=True, poll__org=self.request.org, poll__is_active=True
            )

            if sorted_field in [None, "sdg_track_last_month", "sdg_track_last_week"]:
                sdg_tracked_questions = Dashboard.questions_filter(
                    questions, sorted_field
                )

            context["sdgs_bubble_data"] = Dashboard.get_sdgs_tracked_bubble_chart_data(
                sdg_tracked_questions
            )

            ### SURVEY PARTIAL RESULT CHART ###
            
            # filter only surveys opened
            survey_result_sdg_questions = questions.filter(poll__poll_end_date=datetime.date.today())

            survey_result_sdg = self.request.GET.get("survey_result_sdg")
            
            if survey_result_sdg is None:
                survey_result_sdg_questions = questions
            else:
                survey_result_sdg = int(survey_result_sdg)
                survey_result_sdg_questions = questions.filter(sdgs__contains=[survey_result_sdg])
                context['survey_result_sdg'] = settings.SDG_LIST[survey_result_sdg - 1]
            
            # shuffled questions
            survey_result_sdg_questions = list(survey_result_sdg_questions)
            random.shuffle(survey_result_sdg_questions)

            # max 20 questions
            survey_result_sdg_questions = survey_result_sdg_questions[:20]
            
            context["survey_result_sdg_questions"] = survey_result_sdg_questions
            
            if len(survey_result_sdg_questions) > 0:
                survey_result_raffled_question = survey_result_sdg_questions[0]
                context["survey_result_raffled_question"] = survey_result_raffled_question

                categories = survey_result_raffled_question.get_total_summary_data()['categories']
                total = sum([q['count'] for q in categories])
                
                if total > 0:
                    survey_result_doughnut_data = {
                        'labels': [q['label'] for q in categories],
                        'datasets': [{
                            'data': [round((q['count'] / total) * 100, 2) for q in categories],
                            'backgroundColor': ["#%06x" % random.randint(0, 0xFFFFFF) for i in categories],
                            'borderColor': "rgba(255, 255, 255, 0.1)",
                        }],
                    }

                    context['survey_result_doughnut_data'] = survey_result_doughnut_data

            ### MOST USED CHANNELS CHARTS ###

            ### RAPIDPRO CONTACTS ###

            return context

    class Global(SmartTemplateView):
        template_name = "dashboard/global.html"
