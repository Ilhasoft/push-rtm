import pycountry

from django.db.models import Sum

from smartmin.views import SmartTemplateView
from dash.orgs.models import Org
from ureport.channels.models import ChannelDailyStats


class ListView(SmartTemplateView):
    template_name = "worldmap/index.html"
    permission = "polls_global.poll_list"

    def get_sdgs_from_org(self, org):
        org_sdgs = set()
        for poll in org.polls.all():
            poll_questions = poll.questions.all()
            for question in poll_questions:
                question_sdgs = question.sdgs
                if question_sdgs:
                    question_sdg = set(question_sdgs)
                    org_sdgs = org_sdgs | question_sdg

        return org_sdgs or ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_orgs = Org.objects.all()
        countries_code_alpha2 = {country.name: country.alpha_2 for country in pycountry.countries}

        data_engagement = {}
        data_countries = {}

        for org in all_orgs:
            sent = ChannelDailyStats.objects.filter(msg_direction="O", channel__org=org).aggregate(total=Sum("count"))
            sent = sent.get("total", 0)

            received = ChannelDailyStats.objects.filter(msg_direction="I", channel__org=org).aggregate(total=Sum("count"))
            received = received.get("total", 0)

            engagement = (100 * received) / sent if sent > 0 else 0

            code = countries_code_alpha2.get(org.name).lower()
            if code:

                sdgs_org = self.get_sdgs_from_org(org)

                data_countries[code] = {
                    "org": org,
                    "engagement": round(engagement, 2),
                    "sent": sent,
                    "received": received,
                    "amount_sdgs": len(sdgs_org),
                    "sdgs": sdgs_org,
                    "amount_contacts": len(org.contacts.all()),
                }

                data_engagement[code] = round(engagement, 2)

        context["data_engagement"] = data_engagement
        context["data_countries"] = data_countries

        return context
