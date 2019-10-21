from smartmin.views import SmartTemplateView


class Dashboard:
    class Local(SmartTemplateView):
        template_name = "dashboard/local.html"
    
    class Global(SmartTemplateView):
        template_name = "#"