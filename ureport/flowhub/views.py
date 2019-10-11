import json

from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from smartmin.views import SmartCreateView, SmartListView, SmartTemplateView

from .models import Flow
from .forms import FlowForm


class ListView(SmartListView):
    template_name = 'flowhub/index.html'
    #permission = 'flowhub.flow_list'
    model = Flow
    context_object_name = 'flows'
    #search_fields = ('name__icontains','description__icontains')

    def get_queryset(self):
        queryset = Flow.objects.filter(is_active=True)
        return queryset


class MyOrgListView(SmartListView):
    template_name = 'flowhub/index.html'
    #permission = 'flohub.flow_list'
    model = Flow
    context_object_name = 'flows'

    def get_queryset(self):
        queryset = Flow.objects.filter(is_active=True, org=self.request.org)
        return queryset


class CreateView(SmartCreateView):
    template_name = 'flowhub/form.html'
    #permission = 'flowhub.flow_create'
    model = Flow
    form_class = FlowForm
    success_url = reverse_lazy("flowhub.flow_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_subtitle"] = _("New")
        return context


class DownloadView(SmartTemplateView):
    template_name = "flowhub/info.html"
    #permission = "flowhub.flow_info"

    def get(self, request, *args, **kwargs):
        super().get_context_data(**kwargs)
        flow = (
            Flow.objects.filter(pk=self.kwargs["flow"], is_active=True)
            .filter(Q(org=self.request.org) | Q(visible_globally=True))
            .first()
        )

        if not flow:
            return redirect(reverse("flowhub.flow_list"))

        response = HttpResponse(json.dumps(flow.flow), content_type="application/json")
        response["Content-Disposition"] = "attachment; filename=flow-{}.json".format(flow.pk)

        flow.increase_downloads()

        return response


class DeleteView(SmartTemplateView):
    template_name = 'flowhub/info.html'
    #permission = 'flowhub.flow_info'

    def post(self, request, *args, **kwargs):
        super().get_context_data(**kwargs)

        try:
            flow = Flow.objects.get(
                pk=kwargs.get('flow'),
                is_active = True,
                org = request.org
            )
        except Flow.DoesNotExist:
            flow = None
        
        if not Flow: return redirect(reverse('flowhub.flow_list'))

        flow.is_active = False
        flow.save()
        return redirect(self.request.META.get('HTTP_REFERER'))
