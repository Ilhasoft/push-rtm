from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from dash.orgs.models import Org, OrgBackend
from smartmin.models import SmartModel

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
        org = Org.objects.get(pk=1)
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
