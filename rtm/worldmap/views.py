from smartmin.views import SmartTemplateView
from dash.orgs.views import OrgObjPermsMixin

from rtm.utils import get_messages_sent_org, get_messages_received_org, get_messages_engagement_org, get_sdgs_from_org
from rtm.worldmap.models import OrgCountryCode


class ListView(OrgObjPermsMixin, SmartTemplateView):
    template_name = "worldmap/index.html"
    permission = "orgs.org_manage_accounts"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_country_code = OrgCountryCode.objects.select_related("org")

        data_engagement = {}
        data_countries = {}

        for country_code in all_country_code:
            code = country_code.org_country_code.lower()
            org = country_code.org

            sent = get_messages_sent_org(org)
            received = get_messages_received_org(org)
            engagement = get_messages_engagement_org(sent, received)

            sdgs_org = get_sdgs_from_org(org)

            data_countries[code] = {
                "org_id": org.pk,
                "org_subdomain": org.subdomain,
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
