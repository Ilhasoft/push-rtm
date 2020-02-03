from django.apps import AppConfig


class WorldmapConfig(AppConfig):
    name = 'ureport.worldmap'

    def ready(self):
        import ureport.worldmap.signals
