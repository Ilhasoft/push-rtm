from collections import defaultdict
from datetime import timedelta

from dash.orgs.models import Org

from django.core.cache import cache
from django.db import models
from django.db.models import Count, ExpressionWrapper, F, IntegerField, Q, Sum
from django.db.models.functions import ExtractYear
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from ureport.locations.models import Boundary
from ureport.polls.models import PollQuestion, PollResponseCategory


class GenderSegment(models.Model):

    GENDERS = {"M": _("Male"), "F": _("Female"), "O": _("Other")}

    gender = models.CharField(max_length=1)


class AgeSegment(models.Model):
    min_age = models.IntegerField(null=True)
    max_age = models.IntegerField(null=True)

    @classmethod
    def get_age_segment_min_age(cls, age):
        min_ages = [0, 15, 20, 25, 31, 35]
        return [elt for elt in min_ages if age >= elt][-1]


class PollStats(models.Model):
    DATA_TIME_FILTERS = {3: _("90 Days"), 6: _("6 Months"), 12: _("12 Months")}

    DATA_SEGMENTS = {"all": _("All"), "gender": _("Gender"), "age": _("Age"), "location": _("Location")}

    DATA_METRICS = {
        "opinion-responses": _("Opinion Responses"),
        "sign-up-rate": _("Sign Up Rate"),
        "response-rate": _("Response Rate"),
        "active-users": _("Active Users"),
    }

    id = models.BigAutoField(auto_created=True, primary_key=True, verbose_name="ID")

    org = models.ForeignKey(Org, on_delete=models.PROTECT, related_name="poll_stats")

    question = models.ForeignKey(PollQuestion, null=True, on_delete=models.SET_NULL)

    category = models.ForeignKey(PollResponseCategory, null=True, on_delete=models.SET_NULL)

    age_segment = models.ForeignKey(AgeSegment, null=True, on_delete=models.SET_NULL)

    gender_segment = models.ForeignKey(GenderSegment, null=True, on_delete=models.SET_NULL)

    location = models.ForeignKey(Boundary, null=True, on_delete=models.SET_NULL)

    date = models.DateTimeField(null=True)

    count = models.IntegerField(default=0, help_text=_("Number of items with this counter"))

    @classmethod
    def get_engagement_data(cls, org, metric, segment_slug, time_filter):

        key = f"org:{org.id}:metric:{metric}:segment:{segment_slug}:filter:{time_filter}"
        output_data = cache.get(key, None)
        if output_data:
            return output_data["results"]

        return PollStats.refresh_engagement_data(org, metric, segment_slug, time_filter)

    @classmethod
    def refresh_engagement_data(cls, org, metric, segment_slug, time_filter):

        key = f"org:{org.id}:metric:{metric}:segment:{segment_slug}:filter:{time_filter}"

        output_data = []
        if metric == "opinion-responses":
            if segment_slug == "all":
                output_data = PollStats.get_all_opinion_responses(org, time_filter)
            if segment_slug == "age":
                output_data = PollStats.get_age_opinion_responses(org, time_filter)
            if segment_slug == "gender":
                output_data = PollStats.get_gender_opinion_responses(org, time_filter)
            if segment_slug == "location":
                output_data = PollStats.get_location_opinion_responses(org, time_filter)

        if metric == "sign-up-rate":
            if segment_slug == "all":
                output_data = org.get_sign_up_rate(time_filter)
            if segment_slug == "age":
                output_data = org.get_sign_up_rate_age(time_filter)
            if segment_slug == "gender":
                output_data = org.get_sign_up_rate_gender(time_filter)
            if segment_slug == "location":
                output_data = org.get_sign_up_rate_location(time_filter)

        if metric == "response-rate":
            if segment_slug == "all":
                output_data = PollStats.get_all_response_rate_series(org, time_filter)
            if segment_slug == "age":
                output_data = PollStats.get_age_response_rate_series(org, time_filter)
            if segment_slug == "gender":
                output_data = PollStats.get_gender_response_rate_series(org, time_filter)
            if segment_slug == "location":
                output_data = PollStats.get_location_response_rate_series(org, time_filter)

        if metric == "active-users":
            if segment_slug == "all":
                output_data = ContactActivity.get_activity(org, time_filter)
            if segment_slug == "age":
                output_data = ContactActivity.get_activity_age(org, time_filter)
            if segment_slug == "gender":
                output_data = ContactActivity.get_activity_gender(org, time_filter)
            if segment_slug == "location":
                output_data = ContactActivity.get_contact_activity_location(org, time_filter)

        if output_data:
            cache.set(key, {"results": output_data}, None)
        return output_data

    @classmethod
    def get_all_opinion_responses(cls, org, time_filter):
        responses = PollStats.objects.filter(org=org).exclude(category=None).values("date").annotate(Sum("count"))
        return [dict(name="Opinion Responses", data=PollStats.get_counts_data(responses, time_filter))]

    @classmethod
    def get_gender_opinion_responses(cls, org, time_filter):
        now = timezone.now()
        year_ago = now - timedelta(days=365)
        start = year_ago.replace(day=1)

        genders = GenderSegment.objects.all()
        if not org.get_config("common.has_extra_gender"):
            genders = genders.exclude(gender="O")

        genders = genders.values("gender", "id")

        output_data = []
        for gender in genders:
            responses = (
                PollStats.objects.filter(org=org, date__gte=start, gender_segment_id=gender["id"])
                .exclude(category=None)
                .values("date")
                .annotate(Sum("count"))
            )
            series = PollStats.get_counts_data(responses, time_filter)
            output_data.append(dict(name=str(GenderSegment.GENDERS.get(gender["gender"])), data=series))
        return output_data

    @classmethod
    def get_location_opinion_responses(cls, org, time_filter):
        now = timezone.now()
        year_ago = now - timedelta(days=365)
        start = year_ago.replace(day=1)

        top_boundaries = Boundary.get_org_top_level_boundaries_name(org)
        output_data = []
        for osm_id, name in top_boundaries.items():
            boundary_ids = list(
                Boundary.objects.filter(org=org)
                .filter(Q(osm_id=osm_id) | Q(parent__osm_id=osm_id) | Q(parent__parent__osm_id=osm_id))
                .values_list("pk", flat=True)
            )
            responses = (
                PollStats.objects.filter(org=org, date__gte=start, location_id__in=boundary_ids)
                .exclude(category=None)
                .values("date")
                .annotate(Sum("count"))
            )
            series = PollStats.get_counts_data(responses, time_filter)
            output_data.append(dict(name=name, osm_id=osm_id, data=series))
        return output_data

    @classmethod
    def get_age_opinion_responses(cls, org, time_filter):
        now = timezone.now()
        year_ago = now - timedelta(days=365)
        start = year_ago.replace(day=1)

        ages = AgeSegment.objects.all().values("id", "min_age", "max_age")
        output_data = []
        for age in ages:
            if age["min_age"] == 0:
                data_key = "0-14"
            elif age["min_age"] == 15:
                data_key = "15-19"
            elif age["min_age"] == 20:
                data_key = "20-24"
            elif age["min_age"] == 25:
                data_key = "25-30"
            elif age["min_age"] == 31:
                data_key = "31-34"
            elif age["min_age"] == 35:
                data_key = "35+"

            responses = (
                PollStats.objects.filter(org=org, date__gte=start, age_segment_id=age["id"])
                .exclude(category=None)
                .values("date")
                .annotate(Sum("count"))
            )
            series = PollStats.get_counts_data(responses, time_filter)
            output_data.append(dict(name=data_key, data=series))
        return output_data

    @classmethod
    def get_counts_data(cls, stats_qs, time_filter):
        from ureport.utils import get_last_months

        keys = get_last_months(months_num=time_filter)

        responses_data_dict = defaultdict(int)
        for elt in stats_qs:
            key = str(elt["date"].replace(day=1).date())
            responses_data_dict[key] += elt["count__sum"]

        data = dict()
        for key in keys:
            data[key] = responses_data_dict[key]

        return data

    @classmethod
    def get_all_response_rate_series(cls, org, time_filter):
        now = timezone.now()
        year_ago = now - timedelta(days=365)
        start = year_ago.replace(day=1)

        polled_stats = PollStats.objects.filter(org=org, date__gte=start).values("date").annotate(Sum("count"))
        responded_stats = (
            PollStats.objects.filter(org=org, date__gte=start)
            .exclude(category=None)
            .values("date")
            .annotate(Sum("count"))
        )

        return [
            dict(
                name="Response Rate", data=PollStats.get_response_rate_data(polled_stats, responded_stats, time_filter)
            )
        ]

    @classmethod
    def get_location_response_rate_series(cls, org, time_filter):
        now = timezone.now()
        year_ago = now - timedelta(days=365)
        start = year_ago.replace(day=1)

        top_boundaries = Boundary.get_org_top_level_boundaries_name(org)
        output_data = []
        for osm_id, name in top_boundaries.items():
            boundary_ids = list(
                Boundary.objects.filter(org=org)
                .filter(Q(osm_id=osm_id) | Q(parent__osm_id=osm_id) | Q(parent__parent__osm_id=osm_id))
                .values_list("pk", flat=True)
            )
            polled_stats = (
                PollStats.objects.filter(org=org, date__gte=start, location_id__in=boundary_ids)
                .values("date")
                .annotate(Sum("count"))
            )
            responded_stats = (
                PollStats.objects.filter(org=org, date__gte=start, location_id__in=boundary_ids)
                .exclude(category=None)
                .values("date")
                .annotate(Sum("count"))
            )
            series = PollStats.get_response_rate_data(polled_stats, responded_stats, time_filter)
            output_data.append(dict(name=name, osm_id=osm_id, data=series))
        return output_data

    @classmethod
    def get_gender_response_rate_series(cls, org, time_filter):
        now = timezone.now()
        year_ago = now - timedelta(days=365)
        start = year_ago.replace(day=1)

        genders = GenderSegment.objects.all()
        if not org.get_config("common.has_extra_gender"):
            genders = genders.exclude(gender="O")

        genders = genders.values("gender", "id")

        output_data = []
        for gender in genders:
            polled_stats = (
                PollStats.objects.filter(org=org, date__gte=start, gender_segment_id=gender["id"])
                .values("date")
                .annotate(Sum("count"))
            )
            responded_stats = (
                PollStats.objects.filter(org=org, date__gte=start, gender_segment_id=gender["id"])
                .exclude(category=None)
                .values("date")
                .annotate(Sum("count"))
            )
            gender_rate_series = PollStats.get_response_rate_data(polled_stats, responded_stats, time_filter)
            output_data.append(dict(name=str(GenderSegment.GENDERS.get(gender["gender"])), data=gender_rate_series))

        return output_data

    @classmethod
    def get_age_response_rate_series(cls, org, time_filter):
        now = timezone.now()
        year_ago = now - timedelta(days=365)
        start = year_ago.replace(day=1)

        ages = AgeSegment.objects.all().values("id", "min_age", "max_age")
        output_data = []
        for age in ages:
            if age["min_age"] == 0:
                data_key = "0-14"
            elif age["min_age"] == 15:
                data_key = "15-19"
            elif age["min_age"] == 20:
                data_key = "20-24"
            elif age["min_age"] == 25:
                data_key = "25-30"
            elif age["min_age"] == 31:
                data_key = "31-34"
            elif age["min_age"] == 35:
                data_key = "35+"

            polled_stats = (
                PollStats.objects.filter(org=org, date__gte=start, age_segment_id=age["id"])
                .values("date")
                .annotate(Sum("count"))
            )
            responded_stats = (
                PollStats.objects.filter(org=org, date__gte=start, age_segment_id=age["id"])
                .exclude(category=None)
                .values("date")
                .annotate(Sum("count"))
            )
            age_rate_series = PollStats.get_response_rate_data(polled_stats, responded_stats, time_filter)
            output_data.append(dict(name=data_key, data=age_rate_series))
        return output_data

    @classmethod
    def get_response_rate_data(cls, polled_qs, responded_qs, time_filter):
        from ureport.utils import get_last_months

        keys = get_last_months(months_num=time_filter)

        polled_data_dict = defaultdict(int)
        for elt in polled_qs:
            key = str(elt["date"].replace(day=1).date())
            polled_data_dict[key] += elt["count__sum"]

        responded_data_dict = defaultdict(int)
        for elt in responded_qs:
            key = str(elt["date"].replace(day=1).date())
            responded_data_dict[key] += elt["count__sum"]

        data = dict()
        for key in keys:
            responded = responded_data_dict.get(key)
            polled = polled_data_dict.get(key)
            if responded is None or polled is None or polled == 0:
                rate = 0
            else:
                rate = round(responded * 100 / polled, 2)
            data[key] = rate

        return data

    @classmethod
    def get_average_response_rate(cls, org):

        polled_stats = PollStats.objects.filter(org=org).aggregate(Sum("count"))
        responded_stats = PollStats.objects.filter(org=org).exclude(category=None).aggregate(Sum("count"))

        responded = responded_stats.get("count__sum", 0)
        if responded is None:
            responded = 0
        polled = polled_stats.get("count__sum")
        if polled is None or polled == 0:
            return 0

        return responded * 100 / polled


class ContactActivity(models.Model):
    org = models.ForeignKey(Org, on_delete=models.PROTECT, related_name="contact_activities")

    contact = models.CharField(max_length=36)

    born = models.IntegerField(null=True)

    gender = models.CharField(max_length=1, null=True)

    state = models.CharField(max_length=255, null=True)

    district = models.CharField(max_length=255, null=True)

    ward = models.CharField(max_length=255, null=True)

    date = models.DateField(help_text="The starting date for for the month")

    class Meta:
        index_together = (("org", "contact"), ("org", "date"))
        unique_together = ("org", "contact", "date")

    @classmethod
    def get_activity_data(cls, activities_qs, time_filter):
        from ureport.utils import get_last_months

        keys = get_last_months(months_num=time_filter)

        activity_data = defaultdict(int)
        for elt in activities_qs:
            key = str(elt["date"].replace(day=1))
            activity_data[key] += elt["id__count"]

        data = dict()
        for key in keys:
            data[key] = activity_data[key]

        return dict(data)

    @classmethod
    def get_activity(cls, org, time_filter):
        now = timezone.now()
        today = now.date()
        year_ago = now - timedelta(days=365)
        start = year_ago.replace(day=1).date()

        activities = (
            ContactActivity.objects.filter(org=org, date__lte=today, date__gte=start)
            .values("date")
            .annotate(Count("id"))
        )
        return [dict(name="Active Users", data=ContactActivity.get_activity_data(activities, time_filter))]

    @classmethod
    def get_activity_age(cls, org, time_filter):
        now = timezone.now()
        today = now.date()
        year_ago = now - timedelta(days=365)
        start = year_ago.replace(day=1).date()

        ages = AgeSegment.objects.all().values("id", "min_age", "max_age")
        output_data = []
        for age in ages:
            if age["min_age"] == 0:
                data_key = "0-14"
            elif age["min_age"] == 15:
                data_key = "15-19"
            elif age["min_age"] == 20:
                data_key = "20-24"
            elif age["min_age"] == 25:
                data_key = "25-30"
            elif age["min_age"] == 31:
                data_key = "31-34"
            elif age["min_age"] == 35:
                data_key = "35+"

            activities = (
                ContactActivity.objects.filter(org=org, date__lte=today, date__gte=start)
                .exclude(born=None)
                .exclude(date=None)
                .annotate(year=ExtractYear("date"))
                .annotate(age=ExpressionWrapper(F("year") - F("born"), output_field=IntegerField()))
                .filter(age__gte=age["min_age"], age__lte=age["max_age"])
                .values("date")
                .annotate(Count("id"))
            )
            series = ContactActivity.get_activity_data(activities, time_filter)
            output_data.append(dict(name=data_key, data=series))
        return output_data

    @classmethod
    def get_activity_gender(cls, org, time_filter):
        now = timezone.now()
        today = now.date()
        year_ago = now - timedelta(days=365)
        start = year_ago.replace(day=1).date()

        genders = GenderSegment.objects.all()
        if not org.get_config("common.has_extra_gender"):
            genders = genders.exclude(gender="O")

        genders = genders.values("gender", "id")

        output_data = []
        for gender in genders:
            activities = (
                ContactActivity.objects.filter(org=org, date__lte=today, date__gte=start, gender=gender["gender"])
                .values("date")
                .annotate(Count("id"))
            )
            series = ContactActivity.get_activity_data(activities, time_filter)
            output_data.append(dict(name=str(GenderSegment.GENDERS.get(gender["gender"])), data=series))

        return output_data

    @classmethod
    def get_contact_activity_location(cls, org, time_filter):
        now = timezone.now()
        today = now.date()
        year_ago = now - timedelta(days=365)
        start = year_ago.replace(day=1).date()

        top_boundaries = Boundary.get_org_top_level_boundaries_name(org)
        output_data = []
        for osm_id, name in top_boundaries.items():
            activities = (
                ContactActivity.objects.filter(org=org, date__lte=today, date__gte=start, state=osm_id)
                .values("date")
                .annotate(Count("id"))
            )
            series = ContactActivity.get_activity_data(activities, time_filter)
            output_data.append(dict(name=name, osm_id=osm_id, data=series))
        return output_data
