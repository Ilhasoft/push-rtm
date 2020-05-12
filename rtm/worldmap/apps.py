from django.apps import AppConfig


class WorldmapConfig(AppConfig):
    name = "rtm.worldmap"

    def ready(self):
        import rtm.worldmap.signals
