import random
import datetime
import calendar

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import utc
from django.db.models import Sum, Count
from django.db.models.functions import ExtractMonth, ExtractYear
from django.views.generic import View
from django.http import JsonResponse

from smartmin.views import SmartTemplateView
from dash.orgs.models import Org

from rtm.polls.models import PollQuestion, Poll
from rtm.channels.models import ChannelStats, ChannelDailyStats
from rtm.contacts.models import Contact


class DashboardDataView(View):
    access_level = None

    def get(self, request, *args, **kwargs):
        card = self.request.GET.get("card")
        filter_by = self.request.GET.get("filter_by")

        if request.user.is_authenticated:
            if request.user.is_superuser or request.user.groups.filter(name="Global Viewers"):
                self.access_level = "global"
            elif request.org in request.user.get_user_orgs():
                self.access_level = "local"

        response = dict()
        response["time_ago"] = Dashboard.get_text_time_ago(filter_by)

        if card == "sdg_tracked":
            questions = PollQuestion.objects.filter(is_active=True, poll__is_active=True)

            if self.access_level == "local":
                questions = questions.filter(poll__org=self.request.org)

            if filter_by is None:
                filter_by = "year"

            sdg_tracked_questions = questions

            if filter_by in ["week", "month", "year"]:
                sdg_tracked_questions = Dashboard.questions_filter(questions, created_on=filter_by)

            response["filter_by"] = filter_by
            response["sdgs_bubble_data"] = Dashboard.get_sdgs_tracked_bubble_chart_data(sdg_tracked_questions)

        if card == "partial_results":
            survey_result_sdg = self.request.GET.get("sdg")
            questions = PollQuestion.objects.filter(is_active=True, poll__is_active=True)

            if self.access_level == "local":
                questions = questions.filter(poll__org=self.request.org)

            survey_result_sdg_questions = questions.filter(
                poll__poll_end_date=datetime.datetime.utcnow().replace(tzinfo=utc)
            )

            if survey_result_sdg is None:
                survey_result_sdg_questions = questions
            else:
                survey_result_sdg = int(survey_result_sdg)
                survey_result_sdg_questions = questions.filter(sdgs__contains=[survey_result_sdg])
                response["survey_result_sdg"] = settings.SDG_LIST[survey_result_sdg - 1]

            survey_result_sdg_questions = [q for q in survey_result_sdg_questions if q.get_responded() > 0]

            survey_result_sdg_questions = list(survey_result_sdg_questions)
            random.shuffle(survey_result_sdg_questions)

            questions = []
            for question in survey_result_sdg_questions[:20]:
                word_cloud = []
                statistics = {}

                if question.is_open_ended():
                    for category in question.get_results()[0].get("categories"):
                        count = category.get("count")
                        word_cloud.append(
                            {"text": category.get("label").upper(), "size": count if count > 10 else 20 + count}
                        )
                else:
                    labels = []
                    series = []
                    counts = []

                    results = question.get_results()[0]
                    categories = results.get("categories")
                    for category in categories:
                        labels.append(category.get("label"))
                        series.append("{0:.0f}".format(category.get("count") / results.get("set") * 100))
                        counts.append(category.get("count"))

                    statistics["labels"] = labels
                    statistics["series"] = series
                    statistics["counts"] = counts

                questions.append(
                    {
                        "id": question.pk,
                        "title": question.title,
                        "url": reverse("results.poll_read", args=[question.poll.pk]),
                        "is_open_ended": question.is_open_ended(),
                        "word_cloud": word_cloud,
                        "statistics": statistics,
                    }
                )
            response["questions_count"] = len(questions)
            response["questions"] = questions

        if card == "message_metrics":
            channel_type = self.request.GET.get("type")
            channels = ChannelStats.objects.all().order_by("channel_type")

            if self.access_level == "local":
                channels = channels.filter(org=self.request.org)

            channels_info = {}
            channels_data = {}

            for channel in channels:
                channels_info[channel.channel_type] = {
                    "type": channel.channel_type,
                    "name": Dashboard.channel_info(channel.channel_type, "name"),
                    "icon": Dashboard.channel_info(channel.channel_type, "icon"),
                }

            response["channels_info"] = channels_info

            for channel in channels:
                total = ChannelDailyStats.objects.filter(
                    channel=channel, **Dashboard.filter_by_date("date", filter_by)
                ).aggregate(total=Sum("count"))["total"]

                global_total = (
                    ChannelDailyStats.objects.filter(
                        channel__channel_type=channel.channel_type,
                        **Dashboard.filter_by_date("date", filter_by)
                    ).aggregate(total=Sum("count"))["total"]
                )

                if channel.channel_type not in channels_data:
                    channels_data[channel.channel_type] = {
                        "type": channel.channel_type,
                        "name": Dashboard.channel_info(channel.channel_type, "name"),
                        "icon": Dashboard.channel_info(channel.channel_type, "icon"),
                        "total": 0,
                        "global": global_total if global_total is not None else 0,
                    }

                channels_data[channel.channel_type]["total"] += total if total is not None else 0

            if channel_type:
                channels = channels.filter(channel_type=channel_type)

            channels_stats = ChannelDailyStats.objects.filter(
                channel__in=channels,
                msg_direction__in=["I", "O", "E"],
                msg_type__in=["M", "I", "E"],
                **Dashboard.filter_by_date("date", filter_by),
            ).order_by("date")

            if self.access_level == "local":
                channels_stats = channels_stats.filter(channel__org=self.request.org)

            labels = []
            series = {"O": {}, "I": {}, "E": {}}
            key = ""

            for stats in channels_stats:
                if filter_by == "year" or filter_by == "":
                    key = stats.date.strftime("%B/%Y")
                else:
                    key = stats.date.strftime("%d/%m")

                if key not in series["O"]:
                    series["O"][key] = 0

                if key not in series["I"]:
                    series["I"][key] = 0

                if key not in series["E"]:
                    series["E"][key] = 0

                labels.append(key)
                series[stats.msg_direction][key] += stats.count

            response["channels_stats"] = {"labels": list(dict.fromkeys(labels)), "series": series}
            response["channels_data"] = channels_data
            response["channel_type"] = channel_type
            response["filter_by"] = filter_by

        if card == "channel_most_used":
            most_used = ChannelDailyStats.objects.filter(
                msg_direction__in=["I", "O"], msg_type__in=["M", "I"], **Dashboard.filter_by_date("date", filter_by)
            )

            if self.access_level == "local":
                most_used = most_used.filter(channel__org=self.request.org)

            most_used = (
                most_used.filter().values("channel__channel_type").annotate(total=Sum("count")).order_by("-total")[:3]
            )

            most_used_global = (
                ChannelDailyStats.objects.filter(
                    msg_direction__in=["I", "O"],
                    msg_type__in=["M", "I"],
                    **Dashboard.filter_by_date("date", filter_by),
                )
                .values("channel__channel_type")
                .annotate(total=Sum("count"))
                .order_by("-total")[:3]
            )

            channels_most_used = []
            channels_most_used_global = []

            for channel in most_used:
                channels_most_used.append(
                    {
                        "name": Dashboard.channel_info(channel.get("channel__channel_type"), "name"),
                        "total": channel.get("total", 0),
                    }
                )

            for channel in most_used_global:
                channels_most_used_global.append(
                    {
                        "name": Dashboard.channel_info(channel.get("channel__channel_type"), "name"),
                        "total": channel.get("total", 0),
                    }
                )

            response["channels_most_used"] = channels_most_used
            response["channels_most_used_global"] = channels_most_used_global

        if card == "rapidpro_contacts":
            contacts_over_time = (
                Contact.objects.filter(
                    registered_on__gte=datetime.datetime.utcnow().replace(tzinfo=utc) - datetime.timedelta(days=180)
                )
                .annotate(month=ExtractMonth("registered_on"), year=ExtractYear("registered_on"))
                .order_by("year", "month")
                .values("month", "year")
                .annotate(total=Count("*"))
                .values("month", "year", "total", "org")
            )

            labels = []
            series = {"local": {}, "global": {}}
            key = ""

            for contact in contacts_over_time:
                key = calendar.month_name[contact.get("month")]
                labels.append(key)

                if key not in series["local"]:
                    series["local"][key] = 0

                if key not in series["global"]:
                    series["global"][key] = 0

                scope = "global"
                if self.request.org and contact.get("org") == self.request.org.id:
                    scope = "local"

                if series["global"].get(key):
                    series["global"][key] += contact.get("total")
                else:
                    series[scope][key] = contact.get("total")

            response["contacts_over_time"] = {"labels": list(dict.fromkeys(labels)), "series": series}

            response["global_total_contacts"] = {
                "local": Contact.objects.filter(org=self.request.org).count(),
                "global": Contact.objects.all().count(),
            }

        return JsonResponse(response)


class Dashboard(SmartTemplateView):
    template_name = "dashboard/dashboard.html"

    @classmethod
    def get_sdgs_tracked_bubble_chart_data(self, questions):
        tracked_sdg = []
        not_tracked_sdg = []
        datasets = []

        sdgs_with_data = {
            sdg[0]: {"questions": [q for q in questions if sdg[0] in q.sdgs]} for sdg in settings.SDG_LIST
        }

        total_response_all_sdgs = 0
        for key, value in sdgs_with_data.items():
            if value.get("questions"):
                tracked_sdg.append(settings.SDG_LIST[key - 1])
                for question in value.get("questions"):
                    total_response_all_sdgs += question.get_responded()

                    if "total_responded" not in sdgs_with_data[key]:
                        sdgs_with_data[key]["total_responded"] = 0

                    sdgs_with_data[key]["total_responded"] += question.get_responded()
            else:
                not_tracked_sdg.append(settings.SDG_LIST[key - 1])

        for key, value in tuple(tracked_sdg):
            datasets.append(
                {
                    "sdg": value,
                    "label": "SDG{}".format(key),
                    "data": [{"r": sdgs_with_data.get(key).get("total_responded", 0)}],
                    "backgroundColor": settings.SDG_COLOR.get(key),
                    "borderColor": "#FFFFFF",
                }
            )

        data = {"tracked_sdgs": tuple(tracked_sdg), "not_tracked_sdgs": tuple(not_tracked_sdg), "datasets": datasets}

        return data

    @classmethod
    def questions_filter(self, questions, **kwargs):
        filters = {}
        created_on = kwargs.get("created_on")

        if created_on:
            now = datetime.datetime.utcnow().replace(tzinfo=utc)
            one_year_ago = now - datetime.timedelta(days=365)
            one_moth_ago = now - datetime.timedelta(days=30)
            one_week_ago = now - datetime.timedelta(days=7)

            if created_on == "year":
                filters["created_on__gte"] = one_year_ago
            elif created_on == "month":
                filters["created_on__gte"] = one_moth_ago
            elif created_on == "week":
                filters["created_on__gte"] = one_week_ago

        questions = questions.filter(**filters)

        return questions

    @classmethod
    def filter_by_date(self, date_field, time_ago):
        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        one_year_ago = now - datetime.timedelta(days=365)
        one_month_ago = now - datetime.timedelta(days=30)
        one_week_ago = now - datetime.timedelta(days=7)

        filters = {}

        if time_ago == "year":
            filters[f"{date_field}__gte"] = one_year_ago
        elif time_ago == "month":
            filters[f"{date_field}__gte"] = one_month_ago
        elif time_ago == "week":
            filters[f"{date_field}__gte"] = one_week_ago

        return filters

    @classmethod
    def get_text_time_ago(self, time_ago):
        if time_ago == "year":
            return _("Last 12 months")
        elif time_ago == "month":
            return _("Last 30 days")
        elif time_ago == "week":
            return _("Last 7 days")
        return _("Since Inception")

    @classmethod
    def channel_info(self, urn, field):
        return dict(settings.CHANNEL_TYPES).get(urn).get(field)

    def get(self, request, *args, **kwargs):
        self.access_level = None
        if request.user.is_authenticated:
            if request.user.is_superuser or request.user.groups.filter(name="Global Viewers"):
                self.access_level = "global"
            elif request.org in request.user.get_user_orgs():
                self.access_level = "local"
        else:
            return redirect(reverse("users.user_login"))

        if self.access_level is None:
            return redirect(reverse("blocked"))

        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["access_level"] = self.access_level

        channels_info = {}
        channels = ChannelStats.objects.all().order_by("channel_type")
        if self.access_level == "local":
            channels = channels.filter(org=self.request.org)

        for channel in channels:
            channels_info[channel.channel_type] = {
                "type": channel.channel_type,
                "name": Dashboard.channel_info(channel.channel_type, "name"),
                "icon": Dashboard.channel_info(channel.channel_type, "icon"),
            }

        context["channels_info"] = channels_info

        if self.access_level == "local":
            context["surveys_local_total"] = Poll.objects.filter(org=self.request.org, is_active=True).count()
            context["surveys_global_total"] = Poll.objects.filter(is_active=True).count()
        else:
            context["orgs_total"] = Org.objects.all().count()
            context["orgs_name"] = Org.objects.all().values_list("name", flat=True).order_by("name")

        return context
