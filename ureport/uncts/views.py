from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic.base import RedirectView

from smartmin.views import SmartTemplateView
from dash.orgs.models import Org

from ureport.utils import get_paginator, log_save

from .forms import UnctForm


class ListView(SmartTemplateView):
    template_name = "uncts/index.html"
    permission = "uncts.unct_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("query", "")
        sort_field = self.request.GET.get("sort")
        sort_direction = self.request.GET.get("dir")
        page = self.request.GET.get("page")

        filters = {}
        sortered = "name"

        if query:
            filters["name__icontains"] = query

        if sort_field:
            sortered = "{}{}".format("-" if sort_direction == "desc" else "", sort_field)

        context["orgs"] = get_paginator(Org.objects.filter(**filters, is_active=True).order_by(sortered), page)
        context["query"] = query
        return context


class CreateView(SmartTemplateView):
    template_name = "uncts/form.html"
    permission = "uncts.unct_create"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = UnctForm()
        context["page_subtitle"] = _("New")
        return context

    def post(self, request, *args, **kwargs):
        form = UnctForm(request.POST, request.FILES)

        if form.is_valid():
            instance = form.save(request.user)
            messages.success(request, _("UNCT created with success!"))
            log_save(self.request.user, instance, 1)
            return redirect(reverse("uncts.unct_list"))
        else:
            context = self.get_context_data()
            context["form"] = form
            messages.error(request, form.non_field_errors())
            messages.error(request, _("Sorry, you did not complete the registration."))
            return render(request, self.template_name, context)


class EditView(SmartTemplateView):
    template_name = "uncts/form.html"
    permission = "uncts.unct_update"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        unct = get_object_or_404(Org, pk=self.kwargs["unct"])
        config = unct.config.get("rapidpro")

        data = {
            "name": unct.name,
            "language": unct.language,
            "subdomain": unct.subdomain,
            "timezone": unct.timezone,
            "host": unct.backends.first().host,
            "api_token": unct.backends.first().api_token,
            "born_label": config.get("born_label", ""),
            "male_label": config.get("male_label", ""),
            "ward_label": config.get("ward_label", ""),
            "state_label": config.get("state_label", ""),
            "female_label": config.get("female_label", ""),
            "gender_label": config.get("gender_label", ""),
            "district_label": config.get("district_label", ""),
            "reporter_group": config.get("reporter_group", ""),
            "occupation_label": config.get("occupation_label", ""),
            "registration_label": config.get("registration_label", ""),
        }

        context["form"] = UnctForm(initial=data)
        context["page_subtitle"] = _("Edit {}".format(unct.name))
        return context

    def post(self, request, *args, **kwargs):
        unct = get_object_or_404(Org, pk=self.kwargs["unct"])
        form = UnctForm(request.POST, request.FILES, instance=unct)

        if form.is_valid():
            instance = form.save(request.user)
            messages.success(request, _("UNCT edited with success!"))
            log_save(self.request.user, instance, 2)
            return redirect(reverse("uncts.unct_list"))
        else:
            context = self.get_context_data()
            context["form"] = form
            messages.error(request, form.non_field_errors())
            messages.error(request, _("Sorry, you did not complete the registration."))
            return render(request, self.template_name, context)


class RedirectUrlWithSubdomainView(RedirectView):
    def get_url(self):
        return self.request.get_host()

    def get_scheme(self):
        return self.request.scheme + "://"

    def build_url_with_subdomain(self, subdomain):
        host_url = self.get_url()
        if subdomain:
            subdomain = subdomain + "."

        url = self.get_scheme() + subdomain + host_url
        return url

    def get_redirect_url(self, *args, **kwargs):
        subdomain = kwargs.get("subdomain", "")
        self.url = self.build_url_with_subdomain(subdomain)
        return super().get_redirect_url(*args, **kwargs)
