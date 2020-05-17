from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ChannelInfo, ChannelStats


@receiver(post_save, sender=ChannelStats)
def populate_channels_info(sender, instance, **kwargs):
    channel_info, created = ChannelInfo.objects.get_or_create(urn=instance.channel_type)
    if created:
        channel_info.name = instance.channel_type
        channel_info.icon = "icon-phone"
        channel_info.save()
