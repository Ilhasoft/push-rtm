import json

from smartmin.views import SmartTemplateView


class Dashboard:
    class Local(SmartTemplateView):
        template_name = "dashboard/local.html"

        def get_mock_data(self):
            """
            for test in templates
            """
            import random
            fake_data = {}
            for i in range(17):
                values = [random.randint(7,70) for n in range(4)]
                fake_data[i+1] = {"x": values[0], "y":values[1], "r":values[2]}
            return fake_data

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            data = self.get_mock_data()
            context["bublle_data"] = data
            return context

    class Global(SmartTemplateView):
        template_name = "dashboard/global.html"
