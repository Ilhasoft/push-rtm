from smartmin.views import SmartTemplateView


class ListView(SmartTemplateView):
    template_name = "worldmap/index.html"
    permission = "polls_global.poll_list"
