from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import JSONField, ArrayField
from django.conf import settings
from django.apps import apps

from dash.orgs.models import Org
from taggit.managers import TaggableManager

from smartmin.models import SmartModel


class Flow(SmartModel):
    name = models.CharField(
        max_length=128, verbose_name=_("Name"), help_text=_("The name for flow")
    )
    description = models.TextField(
        null=False, blank=False, verbose_name=_("Description")
    )
    collected_data = models.TextField(
        null=False,
        blank=False,
        verbose_name=_("Collected Data"),
        help_text=_("What data does this data collect from contacts?"),
    )
    org = models.ForeignKey(
        Org,
        on_delete=models.CASCADE,
        related_name="flows",
        verbose_name=_("UNCT"),
        help_text=_("The organization this flow is part of"),
    )
    tags = TaggableManager(verbose_name=_("Tags"))
    sdgs = ArrayField(
        models.IntegerField(choices=settings.SDG_LIST, blank=False),
        verbose_name=_("SDGs"),
    )
    flow = JSONField()
    visible_globally = models.BooleanField(
        default=False, verbose_name=_("Visible Globally")
    )
    languages = ArrayField(
        models.CharField(
            choices=settings.LANGUAGES,
            blank=False,
            max_length=255,
            verbose_name=_("Languages"),
        )
    )
    downloads = models.IntegerField(default=0)
    stars = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name=_("Stars"))

    class Meta:
        verbose_name = _("Flow")
        verbose_name_plural = _("Flows")

    def __str__(self):
        return "{}".format(self.name)

    def get_sdgs(self):
        return {n: dict(settings.SDG_LIST).get(n) for n in self.sdgs}

    def increase_downloads(self):
        self.downloads += 1
        self.save()

    def increase_stars(self, user):
        self.stars.add(user)

    def decrease_stars(self, user):
        self.stars.remove(user)

    @property
    def stars_count(self):
        return self.stars.all().count()
