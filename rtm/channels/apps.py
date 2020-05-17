from django.apps import AppConfig


class ChannelsConfig(AppConfig):
    name = "rtm.channels"

    def ready(self):
        import rtm.channels.signals
