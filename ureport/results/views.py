import json

from django.http import HttpResponse
from django.conf import settings
from django.views.generic import View
from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404

from smartmin.views import SmartReadView, SmartTemplateView

from ureport.polls.models import Poll, PollQuestion
from ureport.polls_global.models import PollGlobal, PollGlobalSurveys
from ureport.polls.templatetags.ureport import question_segmented_results
from ureport.settings import AVAILABLE_COLORS


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
        queryset = queryset.filter(is_active=True, has_synced=True)
        if not self.request.user.is_superuser:
            queryset = queryset.filter(org=self.request.org)
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


class PollGlobalReadView(SmartTemplateView):
    template_name = "results/global_poll_result.html"
    model = PollGlobal

    def calculate_percent_participating_unct(self, active_uncts, all_uncts):
        return int((active_uncts * 100) / all_uncts) if all_uncts > 0 else 0

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        poll_global = get_object_or_404(PollGlobal, pk=self.kwargs["pk"])

        polls_local = []
        polls_global_surveys = poll_global.polls_global.filter(is_joined=True)
        all_sdgs_arrays = polls_global_surveys.values_list('poll_local__questions__sdgs', flat=True)

        all_orgs = []
        active_orgs = []
        for poll_local_iterator in polls_global_surveys:
            polls_local.append(poll_local_iterator.poll_local)

            org = poll_local_iterator.poll_local.org
            all_orgs.append(org)
            if org.is_active:
                active_orgs.append(org)

        all_sdgs = []
        for sdg_array in all_sdgs_arrays:
            if sdg_array:
                [all_sdgs.append(sdg) for sdg in sdg_array]

        all_sdgs = list(set(all_sdgs))
        all_sdgs.sort()

        amount_all_orgs = len(set(all_orgs))
        amount_active_orgs = len(set(active_orgs))

        context["poll_initial"] = polls_local[0].id if len(polls_local) > 0 else -1
        context["participating_unct"] = self.calculate_percent_participating_unct(amount_active_orgs, amount_all_orgs)
        context["poll_global"] = poll_global
        context["all_local_polls"] = list(polls_local)
        context["all_countries"] = list(set(all_orgs))
        context["num_countries"] = amount_all_orgs
        context["sdgs"] = settings.SDG_LIST
        context["all_sdgs"] = all_sdgs
        return context


class PollGlobalDataView(View):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._response = {}
        self._global_questions = {}
        self._local_questions = []

    def _get_question_results_without_segment(self, question):
        """ Get question data without segment. """
        statistics = {}
        word_cloud = {}
        if question.is_open_ended():
            for category in question.get_results()[0].get("categories"):
                count = category.get("count")
                word_cloud[category.get("label").upper()] = {
                        "text": category.get("label").upper(),
                        "size": count if count > 10 else 20 + count
                    }
        else:
            labels = []
            series = []
            counts = []

            results = question.get_results()[0]
            categories = results.get("categories")
            for category in categories:
                labels.append(category.get("label"))
                series.append("{0:.0f}".format(
                    (category.get("count") / results.get("set") * 100) if results.get("set") else 0
                ))
                counts.append(category.get("count"))

            statistics["labels"] = labels
            statistics["series"] = series
            statistics["counts"] = counts

        dict_result = {
            "statistics": statistics,
            "word_cloud": word_cloud
        }
        return dict_result

    def _get_question_segmented_results(self, question, tag):
        """ Get question data sorted by tag. Tag's example: Age, Gender. """
        return question_segmented_results(question, tag)

    def _get_formated_question_segmented_results(self, question, tag):
        """
        Get the segmented data and format in a dictionary.
        Dictionary data is used for graphics in template.
        """
        results = self._get_question_segmented_results(question, tag)
        categories = []
        series = []
        label = []
        data = []
        for result in results:
            categories.append(result.get("label"))

            for category in result.get("categories"):
                if category.get("label") not in label:
                    label.append(category.get("label"))
                    data.append([category.get("count"), ])
                else:
                    index_label = label.index(category.get("label"))
                    data[index_label].append(category.get("count"))

        for item in label:
            series.append({
                "label": item,
                "data": data[label.index(item)],
                "backgroundColor": AVAILABLE_COLORS[label.index(item)],
                "borderColor": "rgba(255, 255, 255, 0.1)",
            })

        dict_result = {
            "categories": categories,
            "series": series
        }
        return dict_result

    def _sum_values_arrays(self, array_all_values, array_local_values):
        """ Sum values ​​from two arrays. """
        return list(map(lambda x, y: x + y, array_all_values, array_local_values))

    def _generate_global_data(self, question, tag):
        """ Get data from a specific question and add to the overall results. """
        question_dict = self._global_questions.get(question.ruleset_label)
        values = question_dict.get(tag).get("series")
        values_to_return = []
        for value in values:
            current_value = value.get("data")
            loop_value = self._get_formated_question_segmented_results(question, tag).get("series")[
                values.index(value)].get(
                "data")
            new_values_in_array = self._sum_values_arrays(current_value, loop_value)
            values_to_return.append(new_values_in_array)

        return values_to_return

    def _update_global_data(self, question, tag):
        """ Get the data of a question added to the global ones and update data global. """
        new_values = self._generate_global_data(question, tag)
        for values in new_values:
            self._global_questions[question.ruleset_label][tag]["series"][new_values.index(values)]["data"] = values

        return self._global_questions

    def _get_results_in_dict(self, question):
        """ Returns a final dictionary with all necessary information in the template. """
        data_without_segment = self._get_question_results_without_segment(question)
        result_dict = {
            "id": question.pk,
            "is_active": question.is_active,
            "created_on": question.created_on,
            "modified_on": question.modified_on,
            "title": question.title,
            "created_by_id": question.created_by_id,
            "modified_by_id": question.modified_by_id,
            "poll_id": question.poll_id,
            "ruleset_label": question.ruleset_label,
            "url": reverse("results.poll_read", args=[question.poll.pk]),
            "is_open_ended": question.is_open_ended(),
            "word_cloud": data_without_segment.get("word_cloud"),
            "get_responded": question.get_responded(),
            "get_polled": question.get_polled(),
            "sdgs": question.sdgs,
            "statistics": data_without_segment.get("statistics"),
            "age": self._get_formated_question_segmented_results(question, "age"),
            "gender": self._get_formated_question_segmented_results(question, "gender")
        }
        return result_dict

    def get(self, request, *args, **kwargs):
        global_survey = self.kwargs["pk"]
        unct = self.kwargs["unct"]

        polls_local = PollGlobalSurveys.objects.filter(
            poll_global_id=global_survey,
            is_joined=True
        )

        global_poll_local_id = polls_local.values_list("poll_local_id", flat=True)

        global_polls_questions = PollQuestion.objects.filter(
            is_active=True,
            poll_id__in=list(global_poll_local_id),
            poll__is_active=True
        )

        global_survey = polls_local[0].poll_global
        global_flow = global_survey.get_flow().get("results", None)
        global_flow_uuids = [question.get("node_uuids")[0] for question in global_flow]

        for question in global_polls_questions:
            question_dict = self._global_questions.get(question.ruleset_label)
            if question_dict:
                results_question = self._get_question_results_without_segment(question)
                local_data_word_cloud = results_question.get("word_cloud", None)

                if local_data_word_cloud:
                    global_data_word_cloud = question_dict.get("word_cloud")
                    #for local_value in local_data_word_cloud:
                    for key, value in local_data_word_cloud.items():
                        local_label = value.get("text")
                        global_value = global_data_word_cloud.get(local_label, None)
                        if global_value:
                            new_value = global_value.get("size", 0) + value.get("size", 0)
                            self._global_questions[question.ruleset_label]["word_cloud"][local_label]["size"] = new_value
                        else:
                            self._global_questions[question.ruleset_label][local_label] = {
                                "text": local_label,
                                "size": value.get("size")
                            }

                else:
                    value_current_question_array = results_question.get(
                        "statistics").get("counts")
                    values_in_array_statistics = question_dict.get("statistics").get("counts")

                    new_values_in_array_statistics = self._sum_values_arrays(values_in_array_statistics,
                                                                             value_current_question_array)
                    self._global_questions[question.ruleset_label]["statistics"]["counts"] = new_values_in_array_statistics
                    self._update_global_data(question, "age")
                    self._update_global_data(question, "gender")
            else:
                self._global_questions[question.ruleset_label] = (self._get_results_in_dict(question))

        local_poll_questions = PollQuestion.objects.filter(is_active=True, poll_id=unct, poll__is_active=True)
        local_poll_title = local_poll_questions[0].poll.title if local_poll_questions else None

        for question in local_poll_questions:
            if question.ruleset_uuid in global_flow_uuids:
                local_results = self._get_results_in_dict(question)
                local_results["local_poll_title"] = local_poll_title
                self._local_questions.append(local_results)

        self._response["questions_global"] = self._global_questions
        self._response["questions_local"] = self._local_questions
        self._response["number_questions"] = len(self._local_questions)
        self._response["sdgs"] = dict(settings.SDG_LIST)

        return JsonResponse(self._response)
