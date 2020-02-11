from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from dash.orgs.models import Org, OrgBackend
from smartmin.models import SmartModel
from temba_client.v2 import TembaClient

from ureport.polls.models import Poll


class PollGlobal(SmartModel):
    '''org = models.ForeignKey(
        Org, on_delete=models.PROTECT, related_name="polls", help_text=_("The organization this poll is part of")
    )'''

    flow_uuid = models.CharField(max_length=36, help_text=_("The Flow this Poll is based on"))

    poll_date = models.DateField(
        help_text=_("The date to display for this survey.")
    )

    poll_end_date = models.DateField(
        null=True, help_text=_("The date to display for this survey.")
    )

    title = models.CharField(
        max_length=255, help_text=_("The title for this survey."))

    description = models.TextField(null=True, help_text=_("THe description for this survey."))

    def __str__(self):
        return self.title

    def get_flow(self):
        """
        Returns the underlying flow for this poll
        """
        org = Org.objects.first()
        backend = OrgBackend.objects.get(pk=1)
        flows_dict = org.get_flows(backend=backend)
        return flows_dict.get(self.flow_uuid, None)


class PollGlobalSurveys(models.Model):
    poll_global = models.ForeignKey(to=PollGlobal, related_name="polls_global", on_delete=models.PROTECT)

    poll_local = models.ForeignKey(to=Poll, related_name="polls_local", on_delete=models.PROTECT)

    is_joined = models.BooleanField(default=False)

    created_on = models.DateTimeField(default=timezone.now, editable=False, blank=True,
                                      help_text="When this item was originally created")

    percent_compability = models.FloatField(blank=True, null=True)

    class Meta:
        unique_together = ["poll_global", "poll_local"]

"""
def get_rapidpro_backend_global():
    HOST = "https://rapidpro.ilhasoft.mobi/"
    TOKEN = "8e8ff83e267e0dd0d12ca9de22d57c4846d3364f"

    temba_client = TembaClient(host=HOST, token=TOKEN)
    query_flows = temba_client.get_flows()
    flows = query_flows.all()

    all_flows = dict()
    for flow in flows:
        flow_json = dict()
        flow_json["uuid"] = flow.uuid
        flow_json["date_hint"] = flow.created_on.strftime("%Y-%m-%d")
        flow_json["created_on"] = datetime_to_json_date(flow.created_on)
        flow_json["name"] = flow.name
        flow_json["archived"] = flow.archived
        flow_json["runs"] = flow.runs.active + flow.runs.expired + flow.runs.completed + flow.runs.interrupted
        flow_json["completed_runs"] = flow.runs.completed
        flow_json["results"] = [
            {"key": elt.key, "name": elt.name, "categories": elt.categories, "node_uuids": elt.node_uuids}
            for elt in flow.results
        ]

        all_flows[flow.uuid] = flow_json
    return all_flows
"""


class RapidProBackendGlobal(object):

    def __init__(self):
        self._host = settings.SITE_API_HOST
        self._token = "8e8ff83e267e0dd0d12ca9de22d57c4846d3364f"
        self._temba_client = TembaClient(host=self._host, token=self._token)

    def get_host(self):
        return self._host

    def get_token(self):
        return self._token

    def get_temba_client(self):
        return self._temba_client

    def query_get_flow(self):
        return self._temba_client.get_flows()
"""
    def get_all_flow(self):
        query_get_flow = self.query_get_flow()
        return query_get_flow.all()


    def format_all_flow_structure(self):
        all_flows = dict()
        flows = self.get_all_flow()
        for flow in flows:
            flow_json = dict()
            flow_json["uuid"] = flow.uuid
            flow_json["date_hint"] = flow.created_on.strftime("%Y-%m-%d")
            flow_json["created_on"] = datetime_to_json_date(flow.created_on)
            flow_json["name"] = flow.name
            flow_json["archived"] = flow.archived
            flow_json["runs"] = flow.runs.active + flow.runs.expired + flow.runs.completed + flow.runs.interrupted
            flow_json["completed_runs"] = flow.runs.completed
            flow_json["results"] = [
                {"key": elt.key, "name": elt.name, "categories": elt.categories, "node_uuids": elt.node_uuids}
                for elt in flow.results
            ]
    
            all_flows[flow.uuid] = flow_json
        return all_flows
"""
