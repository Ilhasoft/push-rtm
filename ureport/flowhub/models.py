from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import JSONField, ArrayField
from django.conf import settings

from dash.orgs.models import Org
from taggit.managers import TaggableManager

from smartmin.models import SmartModel


class Flow(SmartModel):
    name = models.CharField(max_length=128, help_text=_('The name for flow'))
    description = models.TextField(null=False, blank=False)
    collected_data = models.TextField(null=False, blank=False, help_text=_('What data does this data collect from contacts?'))
    org = models.ForeignKey(Org, on_delete=models.CASCADE, related_name='flows', help_text=_('The organization this flow is part of'))
    tags = TaggableManager()
    sdgs = ArrayField(models.IntegerField(choices=settings.SDG_LIST, blank=False))
    flow = JSONField()
    visible_globally = models.BooleanField(default=False)
    languages = ArrayField(models.CharField(choices=settings.LANGUAGES, blank=False, max_length=2))
    downloads = models.IntegerField(default=0)

    class Meta:
        verbose_name = _('Flow')
        verbose_name_plural = _('Flows')
    
    def __str__(self):
        return "{}".format(self.name)
    
    def get_sdgs(self):
        return {n :dict(settings.SDG_LIST).get(n) for n in self.sdgs}
    
    def increase_downloads(self):
        self.downloads += 1
        self.save()
