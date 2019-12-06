from django.db import models
from django.utils.translation import ugettext_lazy as _
from smartmin.models import SmartModel


class PollGlobal(SmartModel):
    poll_date = models.DateField(
        help_text=_("The date to display for this survey.")
    )

    poll_end_date = models.DateField(
        null=True, help_text=_("The date to display for this survey.")
    )

    title = models.CharField(
        max_length=255, help_text=_("The title for this Survey"))

    def __str__(self):
        return self.title
