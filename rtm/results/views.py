import json
import csv

from django.http import HttpResponse
from django.conf import settings
from django.views.generic import View
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404, render

from smartmin.views import SmartReadView, SmartTemplateView

from rtm.polls.models import Poll, PollQuestion, PollResult
from rtm.polls.serializers import PollResultSerializer
from rtm.polls_global.models import PollGlobal, PollGlobalSurveys
from rtm.polls.templatetags.rtm import question_segmented_results
from rtm.settings import AVAILABLE_COLORS


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

    def _get_response_data(self, global_survey, unct):
        response = {}

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
        global_flow = global_survey.get_flow().get("results", [])
        global_flow_keys = [question.get("key") for question in global_flow]

        for question in global_polls_questions:
            question_dict = self._global_questions.get(question.ruleset_label)
            if question_dict:
                results_question = self._get_question_results_without_segment(question)
                local_data_word_cloud = results_question.get("word_cloud", None)

                if local_data_word_cloud:
                    global_data_word_cloud = question_dict.get("word_cloud")
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
                    # TODO: instead of adding 2 arrays, use 'categories' and 'counts' to create a
                    #  dictionary and search for each key and its value then add
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
            key = question.ruleset_label.replace(" ", "_").lower()
            if key in global_flow_keys:
                local_results = self._get_results_in_dict(question)
                local_results["local_poll_title"] = local_poll_title
                self._local_questions.append(local_results)

        response["questions_global"] = self._global_questions
        response["questions_local"] = self._local_questions
        response["number_questions"] = len(self._local_questions)
        response["sdgs"] = dict(settings.SDG_LIST)

        return response

    def get(self, request, *args, **kwargs):
        global_survey = self.kwargs["pk"]
        unct = self.kwargs["unct"]
        response = self._get_response_data(global_survey, unct)

        return JsonResponse(response)


class ResultsIFrame(PollGlobalDataView):
    def get(self, request, *args, **kwargs):
        scope_type = request.GET.get("scope-type")
        poll_title = request.GET.get("poll-title")
        question_title = request.GET.get("question-title")
        print(request)

        try:
            if scope_type == "local":
                question = PollQuestion.objects.filter(title=question_title, poll__title=poll_title).first()
                context = self._get_results_in_dict(question)

            elif scope_type == "global":
                poll_global = PollGlobal.objects.get(title=poll_title)
                id_poll_global = poll_global.id or None
                response_complete = self._get_response_data(id_poll_global, 0)
                global_response = response_complete.get("questions_global", {})
                context = global_response.get(question_title)
            else:
                raise

        except Exception as e:
            print(e)
            messages.error(request, "Sorry, an error occurred in the request.")
            context = {}

        data_chart = {
            "word_cloud": context.get("word_cloud", {}),
            "statistics": context.get("statistics", {}),
            "age": context.get("age", {}),
            "gender": context.get("gender", {}),
        }

        return render(request, "results/iframe.html", {
            "context": context,
            "data_chart": json.dumps(data_chart)
        })


class ExportPollResultsBase(View):
    def _get_headers(self):
        return "contact", "category", "text"

    def _is_unct(self):
        return True if self.request.org else False

    def _get_object_survey(self):
        pk = self.kwargs.get("pk")
        cls = Poll if self._is_unct() else PollGlobal
        return cls.objects.get(pk=pk)

    def _get_file_name(self):
        obj = self._get_object_survey()
        return obj.title or "results_survey"

    def _get_poll_results_data(self):
        pk = self.kwargs.get("pk")

        if self._is_unct():
            poll = Poll.objects.get(pk=pk)
            flow_uuid = poll.flow_uuid
            poll_results = PollResult.objects.filter(flow=flow_uuid).select_related()

        else:
            flows_uuid = set()
            global_surveys = PollGlobalSurveys.objects.filter(poll_global=pk)
            for global_survey in global_surveys:
                flow_uuid = {global_survey.poll_local.flow_uuid}
                flows_uuid = flows_uuid | flow_uuid
            poll_results = PollResult.objects.filter(flow__in=list(flows_uuid)).select_related()

        return poll_results


class PollResultsCSV(ExportPollResultsBase):
    def _get_headers(self):
        raw_header = ["Contact ID"]
        ruleset_labels = self._get_ruleset_labels()

        for label in ruleset_labels:
            raw_header.append(label + " (category)")
            raw_header.append(label + " (text)")

        return raw_header

    def _get_ruleset_labels(self):
        pk = self.kwargs.get("pk")
        rulesets = PollQuestion.objects.filter(poll__id=pk).values_list("ruleset_label", flat=True)

        return list(rulesets)

    def _format_poll_results_data(self):
        results_data = list(self._get_poll_results_data())

        formated_data = {}

        for result in results_data:
            contact_uuid, ruleset_question, category, text = result
            dict_question_uuid = {}

            if not formated_data.get(contact_uuid):
                formated_data[contact_uuid] = {}

            dict_question_uuid[ruleset_question] = [category, text]
            formated_data[contact_uuid].update(dict_question_uuid)

        return formated_data

    def _get_poll_results_data(self):
        poll_results = super()._get_poll_results_data().values_list(
                "contact", "ruleset", "category", "text")

        return poll_results

    def _get_raw_results(self):
        formated_result = self._format_poll_results_data()
        raw_results = []

        questions_ruleset_labels = self._get_ruleset_labels()
        for contact_uuid, question_results in formated_result.items():
            raw_result = [contact_uuid,]

            for ruleset_label in questions_ruleset_labels:
                #TODO: DEMORANDO MUITO ESSE FOR
                question = PollQuestion.objects.filter(poll__id=self.kwargs.get("pk"), ruleset_label=ruleset_label)[0]
                ruleset_uuid = question.ruleset_uuid

                results = question_results.get(ruleset_uuid, ["", ""])
                for result in results:
                    raw_result.append(result)

            raw_results.append(raw_result)

        return raw_results

    def get(self, *args, **kwargs):
        response = HttpResponse(content_type="text/csv")

        writer = csv.writer(response)
        writer.writerow(self._get_headers())

        poll_results = self._get_raw_results()
        for result in poll_results:
            writer.writerow(result)

        filename = self._get_file_name()
        response["Content-Disposition"] = f"attachment;filename={filename}.csv"

        return response


class PollResultsJSON(ExportPollResultsBase):

    def get(self, *args, **kwargs):
        poll_results = self._get_poll_results_data()

        serializer_obj = PollResultSerializer(poll_results, many=True).data
        obj_json = json.dumps(serializer_obj, ensure_ascii=False)

        filename = self._get_file_name()
        response = HttpResponse(obj_json, content_type="application/json")
        response["Content-Disposition"] = f"attachment; filename={filename}.json"
        return response
