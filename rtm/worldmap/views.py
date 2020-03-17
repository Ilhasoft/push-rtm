from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist

from smartmin.views import SmartTemplateView
from dash.orgs.views import OrgObjPermsMixin
from dash.orgs.models import Org
from rtm.channels.models import ChannelDailyStats


class ListView(OrgObjPermsMixin, SmartTemplateView):
    template_name = "worldmap/index.html"
    permission = "orgs.org_manage_accounts"

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

        data_engagement = {}
        data_countries = {}

        for org in all_orgs:
            sent = ChannelDailyStats.objects.filter(msg_direction="O", channel__org=org).aggregate(total=Sum("count"))
            sent = sent.get("total", 0) or 0

            received = ChannelDailyStats.objects.filter(msg_direction="I", channel__org=org).aggregate(total=Sum("count"))
            received = received.get("total", 0) or 0

            engagement = (100 * received) / sent if sent > 0 else 0

            code = None
            try:
                code = org.org_country_code.org_country_code.lower()
            except ObjectDoesNotExist:
                pass

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
