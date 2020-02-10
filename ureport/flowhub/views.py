import base64
import json
import operator
from functools import reduce
from urllib.parse import urlparse

from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin

from dash.orgs.models import Org
from smartmin.views import SmartTemplateView

from ureport.utils import get_paginator, is_global_user

from .models import Flow
from .forms import FlowForm


class FlowBreadCrumbListView(SmartTemplateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = self.get_breadcrumb()

        return context

    def get_breadcrumb(self):
        path_and_url = {
            "previous": {
                "url": self.get_previous_url(),
                "path": self.get_previous_path()
            },
            "current": {
                "path": self.get_current_path()
            }
        }
        return path_and_url

    def get_previous_path(self):
        previous_url = self.get_previous_url()
        cleaned_path = self.clean_path(previous_url)
        return cleaned_path

    def get_previous_url(self):
        return self.request.META.get("HTTP_REFERER")

    def get_current_path(self):
        current_url = self.get_current_url()
        cleaned_path = self.clean_path(current_url)
        return cleaned_path

    def get_current_url(self):
        return self.request.build_absolute_uri()

    def clean_path(self, url):
        url_parse = urlparse(url or self.get_current_url())
        cleaned_path = url_parse.path.replace("flowhub", "").replace("/", "")
        cleaned_path = self.replace_path(cleaned_path)
        if url_parse.query:
            try:
                pk = int(url_parse.query.replace("unct=", ""))
                cleaned_path = Org.objects.get(pk=pk).name
            except Exception:
                cleaned_path = ""

        if not cleaned_path:
            cleaned_path = ""

        return cleaned_path

    def replace_path(self, path):
        paths = ["My Org", "Create", "UNCTS", "Info", "Update"]
        path = path.replace("my-org", "My Org").replace("uncts", "UNCTS")
        path = path.replace("create", "Create").replace("info", "Info")
        path = path.replace("update", "Update")

        if path not in paths:
            path = ""

        return path


class SearchSmartListViewMixin(FlowBreadCrumbListView):
    search_query_name = "search"

    def search(self, queryset):
        search_query = self.request.GET.get(self.search_query_name)
        search_fields = self.derive_search_fields()

        if search_fields and search_query:
            term_queries = []
            for term in search_query.split(" "):
                field_queries = []
                for field in search_fields:
                    field_queries.append(Q(**{field: term}))
                term_queries.append(reduce(operator.or_, field_queries))

            queryset = queryset.filter(reduce(operator.and_, term_queries))

        related = self.derive_select_related()
        if related:
            queryset = queryset.select_related(*related)

        return queryset

    def derive_search_fields(self):
        return self.search_fields


class FlowBaseListView(LoginRequiredMixin, SearchSmartListViewMixin):
    search_query_name = "search"
    select_related = None
    fields = "__all__"
    redirect_to = ""
    query = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["languages"] = settings.LANGUAGES
        context["sdgs"] = settings.SDG_LIST
        return context

    def derive_select_related(self):
        return self.select_related

    def get_queryset(self):
        queryset = self.model.objects.filter(is_active=True).order_by("name")

        if not is_global_user(self.request.user):
            queryset = queryset.filter(
                Q(org=self.request.org) | Q(visible_globally=True))

        queryset = self.search(queryset)
        queryset = self.filter(queryset)
        self.query = self.request.GET.get(self.search_query_name, "")
        return queryset

    def filter(self, queryset):
        sort_field = self.request.GET.get("sort")
        sort_direction = self.request.GET.get("dir")
        language = self.request.GET.get("lang", "")
        sdg = self.request.GET.get("sdg", 0)
        unct = self.request.GET.get("unct")

        filters = {}
        sortered = "stars"

        if language:
            filters["languages__contains"] = [language]

        if sdg:
            filters["sdgs__contains"] = [sdg]

        if unct:
            filters["org_id"] = unct

        if sort_field:
            sortered = "{}{}".format(
                "-" if sort_direction == "desc" else "", sort_field)

        return queryset.filter(**filters).order_by(sortered)


class ListView(FlowBaseListView):
    template_name = "flowhub/index.html"
    model = Flow
    search_fields = ["name__icontains", "description__icontains"]
    filter_fields = ["name__icontains", "description__icontains"]
    search_query_name = "search"
    redirect_to = "flowhub.flow_list"

    def derive_url_pattern(path, action):
        return "flowhub/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subtitle"] = _("All flows")
        context["flow_section_id"] = "flowhub-all"

        page = self.request.GET.get("page", 1)
        context["flows"] = get_paginator(list(self.get_queryset()), page)
        context["query"] = self.query
        context["back_to"] = reverse("flowhub.flow_list")
        context["redirect_to"] = str(base64.b64encode(
            context["back_to"].encode("UTF-8")), "UTF-8")
        return context


class UnctsView(SearchSmartListViewMixin):
    template_name = "flowhub/uncts.html"
    model = Org
    context_object_name = "uncts"
    search_fields = ["name__icontains"]
    select_related = None
    query = ""

    def derive_select_related(self):
        return self.select_related

    def get_queryset(self):
        sort_field = self.request.GET.get("sort")
        sort_direction = self.request.GET.get("dir")
        sortered = "name"

        if sort_field:
            sortered = "{}{}".format(
                "-" if sort_direction == "desc" else "", sort_field)

        queryset = self.model.objects.filter(is_active=True).order_by(sortered)
        queryset = self.search(queryset)
        self.query = self.request.GET.get("search", "")

        for org in queryset:
            org.total_stars = sum([f.stars.all().count()
                                   for f in org.flows.filter(is_active=True)])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subtitle"] = _("UNCTs")
        context["flow_section_id"] = "flowhub-uncts"
        page = self.request.GET.get("page", 1)
        context["uncts"] = get_paginator(self.get_queryset(), page)
        context["query"] = self.query
        context["back_to"] = reverse("flowhub.flow_uncts")
        return context


class MyOrgListView(FlowBaseListView):
    template_name = "flowhub/index.html"
    model = Flow
    context_object_name = "flows"
    search_fields = ["name__icontains", "description__icontains"]
    redirect_to = "flowhub.my_org_flow_list"

    def get_queryset(self):
        return super().get_queryset().filter(org=self.request.org)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subtitle"] = "{} {}".format(self.request.org.name, _("flows"))
        context["flow_section_id"] = "flowhub-my-org"

        page = self.request.GET.get("page", 1)
        context["flows"] = get_paginator(list(self.get_queryset()), page)
        context["query"] = self.query
        context["back_to"] = reverse("flowhub.my_org_flow_list")
        context["redirect_to"] = str(base64.b64encode(
            context["back_to"].encode("UTF-8")), "UTF-8")

        return context


class CreateView(FlowBreadCrumbListView):
    template_name = "flowhub/form.html"
    success_url = reverse_lazy("flowhub.flow_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subtitle"] = _("Upload New Flow")
        context["flow_section_id"] = "flowhub-upload"

        context["form"] = FlowForm()
        return context

    def post(self, request, *args, **kwargs):
        form = FlowForm(request.POST, request.FILES)

        if form.is_valid():
            form.save(self.request)
            messages.success(request, _("Flow created with success!"))
            return redirect(reverse("flowhub.flow_list"))
        else:
            context = self.get_context_data()
            context["form"] = form
            messages.error(request, _(
                "Sorry, you did not complete the registration."))
            messages.error(request, form.non_field_errors())
            return render(request, self.template_name, context)


class EditView(FlowBreadCrumbListView):
    template_name = "flowhub/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flow = get_object_or_404(Flow, pk=self.kwargs["flow"])
        data = {
            "name": flow.name,
            "languages": flow.languages,
            "description": flow.description,
            "collected_data": flow.collected_data,
            "tags": list(flow.tags.values_list("name", flat=True)),
            "sdgs": flow.sdgs,
            "visible_globally": flow.visible_globally,
        }

        context["form"] = FlowForm(data=data, flow_is_required=False)
        context["page_subtitle"] = _("Edit")
        return context

    def post(self, request, *args, **kwargs):
        flow = get_object_or_404(Flow, pk=self.kwargs["flow"])
        form = FlowForm(request.POST, request.FILES,
                        instance=flow, flow_is_required=False)

        if form.is_valid():
            form.save(self.request)
            messages.success(request, _("Flow updated with success!"))
            return redirect(reverse("flowhub.flow_list"))
        else:
            context = self.get_context_data()
            context["form"] = form
            messages.error(request, _(
                "Sorry, you did not complete the registration."))
            messages.error(request, form.non_field_errors())
            return render(request, self.template_name, context)


class DownloadView(FlowBreadCrumbListView):
    template_name = "flowhub/info.html"

    def get(self, request, *args, **kwargs):
        super().get_context_data(**kwargs)
        queryset = Flow.objects.filter(pk=self.kwargs["flow"], is_active=True)

        if not is_global_user(self.request.user):
            queryset = queryset.filter(
                Q(org=self.request.org) | Q(visible_globally=True))

        flow = queryset.first()

        if not flow:
            return redirect(reverse("flowhub.flow_list"))

        response = HttpResponse(json.dumps(flow.flow),
                                content_type="application/json")
        response[
            "Content-Disposition"] = "attachment; filename=flow-{}.json".format(flow.pk)

        flow.increase_downloads()

        return response


class StarView(FlowBreadCrumbListView):
    template_name = "flowhub/info.html"

    def get(self, request, *args, **kwargs):
        super().get_context_data(**kwargs)
        flow = Flow.objects.filter(
            pk=self.kwargs["flow"], is_active=True).first()

        if flow:
            flow.decrease_stars(request.user) if request.user in flow.stars.all() else flow.increase_stars(
                request.user
            )

        return redirect(self.request.META.get("HTTP_REFERER"))


class DeleteView(FlowBreadCrumbListView):
    template_name = "flowhub/info.html"

    def post(self, request, *args, **kwargs):
        super().get_context_data(**kwargs)

        try:
            flow = Flow.objects.get(pk=kwargs.get(
                "flow"), is_active=True, org=request.org)
        except Flow.DoesNotExist:
            flow = None

        if not Flow:
            return redirect(reverse("flowhub.flow_list"))

        flow.is_active = False
        flow.save()

        redirect_to = request.POST.get("redirect_to")
        if redirect_to:
            redirect_to = str(base64.b64decode(
                redirect_to.encode("UTF-8")), "UTF-8")
            return redirect(redirect_to)
        return redirect(self.request.META.get("HTTP_REFERER"))


class InfoView(FlowBreadCrumbListView):
    template_name = "flowhub/info.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = Flow.objects.get(pk=kwargs.get("flow"))
        context["redirect_to"] = str(base64.b64encode(
            self.request.META.get("HTTP_REFERER").encode("UTF-8")), "UTF-8")
        context["flow"] = queryset
        return context
