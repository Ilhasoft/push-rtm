import random
import datetime

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import utc
from django.db.models import Sum, Count
from django.db.models.functions import ExtractMonth, ExtractYear

from smartmin.views import SmartTemplateView

from ureport.polls.models import PollQuestion, Poll
from ureport.channels.models import ChannelStats, ChannelDailyStats
from ureport.contacts.models import Contact


class Dashboard(SmartTemplateView):
    template_name = "dashboard/dashboard.html"

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
            # create dict with sdgs and yours questions. eg: {1: {'questions':
            # []}}
            sdgs_with_data = {
                sdg[0]: {"questions": [q for q in questions if sdg[0] in q.sdgs]}
                for sdg in settings.SDG_LIST
            }

            # add keys total_responded and percentage_in_questions to
            # sdgs_with_data
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
    def questions_filter(self, questions, **kwargs):
        filters = {}
        created_on = kwargs.get("created_on")

        # created_on filter
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
            return _("Last Year")
        elif time_ago == "month":
            return _("Last Month")
        elif time_ago == "week":
            return _("Last Week")
        return _("Since Inception")

    @classmethod
    def channel_info(self, urn, field):
        return dict(settings.CHANNEL_TYPES).get(urn).get(field)


    def get(self, request, *args, **kwargs):
        self.access_level = None
        
        if request.user.is_authenticated:
            if request.user.is_superuser:
                self.access_level = 'global'
            elif request.org in request.user.get_user_orgs():
                self.access_level = 'local'
        else:
            return redirect(reverse("users.user_login"))
        
        if self.access_level is None:
            pass  # redirect to home

        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['access_level'] = self.access_level

        channels_metrics_by = self.request.GET.get(
            "message_metrics_by", "week")
        channels_metrics_uuid = self.request.GET.get(
            "message_metrics_uuid", "")

        most_used_by = self.request.GET.get(
            "most_used_by", "week")

        questions = PollQuestion.objects.filter(
            is_active=True, poll__is_active=True
        )

        if self.access_level == 'local':
            questions = questions.filter(poll__org=self.request.org)

        # SDG TRAKED BUBBLE CHART ###
        sdg_tracked_filter = self.request.GET.get("sdg_tracked_filter")
        if sdg_tracked_filter is None:
            sdg_tracked_filter = "year"

        sdg_tracked_questions = questions

        if sdg_tracked_filter in ["week", "month", "year"]:
            sdg_tracked_questions = Dashboard.questions_filter(
                questions, created_on=sdg_tracked_filter
            )

        context["sdg_tracked_filter"] = sdg_tracked_filter
        context["sdgs_bubble_data"] = Dashboard.get_sdgs_tracked_bubble_chart_data(
            sdg_tracked_questions
        )

        # SURVEY PARTIAL RESULT CHART ###

        # filter only surveys opened
        survey_result_sdg_questions = questions.filter(
            poll__poll_end_date=datetime.datetime.utcnow().replace(tzinfo=utc)
        )

        survey_result_sdg = self.request.GET.get("survey_result_sdg")

        if survey_result_sdg is None:
            survey_result_sdg_questions = questions
        else:
            survey_result_sdg = int(survey_result_sdg)
            survey_result_sdg_questions = questions.filter(
                sdgs__contains=[survey_result_sdg]
            )
            context["survey_result_sdg"] = settings.SDG_LIST[
                survey_result_sdg - 1]

        # show only question with data chart
        survey_result_sdg_questions = [q for q in survey_result_sdg_questions if q.get_responded() > 0]

        # shuffled questions
        survey_result_sdg_questions = list(survey_result_sdg_questions)
        random.shuffle(survey_result_sdg_questions)

        survey_result_choice_question = self.request.GET.get(
            "survey_result_choice_question"
        )
        try:
            survey_result_choice_question = PollQuestion.objects.get(
                pk=survey_result_choice_question
            )
        except PollQuestion.DoesNotExist:
            survey_result_choice_question = None

        # max 20 questions
        context["survey_result_sdg_questions"] = survey_result_sdg_questions[:20]

        # MESSAGE METRICS
        channels = ChannelStats.objects.all().order_by("channel_type")

        if self.access_level == 'local':
            channels = channels.filter(org=self.request.org)

        channels_info = {}
        channels_data = {}

        for channel in channels:
            channels_info[channel.uuid] = {
                "name": Dashboard.channel_info(channel.channel_type, "name"),
                "icon": Dashboard.channel_info(channel.channel_type, "icon"),
            }
        context["channels_info"] = channels_info

        for channel in channels:
            total = ChannelDailyStats.objects.filter(
                channel=channel, **Dashboard.filter_by_date("date", channels_metrics_by)
            ).aggregate(
                total=Sum("count")
            )["total"]

            global_total = ChannelDailyStats.objects.exclude(
                channel__org=self.request.org,
            ).filter(
                channel__channel_type=channel.channel_type,
                **Dashboard.filter_by_date("date", channels_metrics_by)
            ).aggregate(
                total=Sum("count")
            )["total"]

            channels_data[channel.uuid] = {
                "name": Dashboard.channel_info(channel.channel_type, "name"),
                "icon": Dashboard.channel_info(channel.channel_type, "icon"),
                "total": total if total is not None else 0,
                "global": global_total if global_total is not None else 0,
            }

        if channels_metrics_uuid:
            channels = channels.filter(uuid=channels_metrics_uuid)

        channels_chart_stats = ChannelDailyStats.objects.filter(
            #channel__org=self.request.org,
            channel__in=channels,
            msg_direction__in=["I", "O", "E"],
            msg_type__in=["M", "I", "E"],
            **Dashboard.filter_by_date("date", channels_metrics_by),
        ).order_by("date")

        if self.access_level == 'local':
            channels_chart_stats = channels_chart_stats.filter(channel__org=self.request.org)

        context["channels_chart_stats"] = channels_chart_stats
        context["channels_data"] = channels_data
        context["channels_metrics_uuid"] = channels_metrics_uuid
        context["channels_metrics_by"] = channels_metrics_by
        context["channels_messages_ago"] = Dashboard.get_text_time_ago(
            channels_metrics_by)

        # MOST USED CHANNELS CHARTS
        context["surveys_total"] = Poll.objects.filter(
            org=self.request.org, is_active=True).count()

        most_used = ChannelDailyStats.objects.filter(
            #channel__org=self.request.org,
            msg_direction__in=["I", "O"],
            msg_type__in=["M", "I"],
            **Dashboard.filter_by_date("date", most_used_by),
        )
        
        if self.access_level == 'local':
            most_used = most_used.filter(
                channel__org=self.request.org,
            )
        
        most_used = most_used.filter().values("channel__channel_type").annotate(total=Sum("count")).order_by("-total")[:3]

        most_used_global = ChannelDailyStats.objects.exclude(
            channel__org=self.request.org,
        ).filter(
            msg_direction__in=["I", "O"],
            msg_type__in=["M", "I"],
            **Dashboard.filter_by_date("date", most_used_by),
        ).values(
            "channel__channel_type"
        ).annotate(
            total=Sum("count")
        ).order_by("-total")[:3]

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

        context["channels_most_used_ago"] = Dashboard.get_text_time_ago(
            most_used_by)
        context["channels_most_used"] = channels_most_used
        context["channels_most_used_global"] = channels_most_used_global

        # RAPIDPRO CONTACTS
        context["contacts_over_time"] = Contact.objects.filter(
            registered_on__gte=datetime.datetime.utcnow().replace(tzinfo=utc) - datetime.timedelta(days=180),
        ).annotate(
            month=ExtractMonth("registered_on"),
            year=ExtractYear("registered_on")).order_by("month").values(
            "month",
            "year"
        ).annotate(total=Count("*")).values(
            "month",
            "year",
            "total",
            "org",
        )

        context["global_total_contacts"] = {
            "local": Contact.objects.filter(org=self.request.org).count(),
            "global": Contact.objects.exclude(org=self.request.org).count(),
        }

        return context
