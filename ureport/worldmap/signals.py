from django.db.models.signals import post_save
from django.dispatch import receiver
from dash.orgs.models import Org
from .tasks import create_org_country_code


@receiver(post_save, sender=Org)
def create_org_country_code_signals(sender, instance, **kwargs):
    create_org_country_code.apply_async(kwargs={"org_id": instance.id})
