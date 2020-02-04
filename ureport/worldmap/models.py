from django.db import models

from dash.orgs.models import Org


class OrgCountryCode(models.Model):
    org_country_code = models.CharField(max_length=2, unique=True)
    org = models.OneToOneField(Org, on_delete=models.CASCADE, related_name="org_country_code")
