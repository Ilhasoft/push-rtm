from django.db import models
from django.contrib.auth.models import User, Group

from dash.orgs.models import Org


class LogPermissionUser(models.Model):
    user = models.ForeignKey(to=User, related_name="logs_permission_user", on_delete=models.PROTECT)

    org = models.ForeignKey(to=Org, related_name="logs_permission_unct", on_delete=models.PROTECT, null=True, blank=True)

    permission = models.ForeignKey(to=Group, related_name="logs_permission", on_delete=models.PROTECT, null=True, blank=True)
