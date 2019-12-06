from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext as _
from smartmin.views import SmartTemplateView
from ureport.utils import get_paginator

from .models import PollGlobal
from .forms import PollGlobalForm


class ListView(SmartTemplateView):
    template_name = "polls_global/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("query", "")
        sort_field = self.request.GET.get("sort")
        sort_direction = self.request.GET.get("dir")
        page = self.request.GET.get("page")

        filters = {}
        sortered = "title"

        if query:
            filters["title__icontains"] = query

        if sort_field:
            sortered = "{}{}".format("-" if sort_direction == "desc" else "", sort_field)

        context["polls"] = get_paginator(PollGlobal.objects.filter(**filters).order_by(sortered), page)
        context["query"] = query
        return context


class CreateView(SmartTemplateView):
    template_name = "polls_global/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = PollGlobalForm()
        context["page_subtitle"] = _("New")
        return context

    def post(self, request, *args, **kwargs):
        form = PollGlobalForm(request.POST, request.FILES)

        if form.is_valid():
            form.save(request.user)
            messages.success(request, _("Survey created with success!"))
            return redirect(reverse("polls_global.poll_list"))
        else:
            context = self.get_context_data()
            context["form"] = form
            messages.error(request, form.non_field_errors())
            messages.error(request, _("Sorry, you did not complete the registration."))
            return render(request, self.template_name, context)


class EditView(SmartTemplateView):
    template_name = "polls_global/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        poll = get_object_or_404(PollGlobal, pk=self.kwargs.get("poll"))

        data = {
            "title": poll.title,
            "poll_date": poll.poll_date,
            "poll_end_date": poll.poll_end_date,
            "is_active": poll.is_active,
        }

        context["form"] = PollGlobalForm(initial=data)
        context["page_subtitle"] = _("Edit {}".format(poll.title))
        return context

    def post(self, request, *args, **kwargs):
        poll = get_object_or_404(PollGlobal, pk=self.kwargs.get("poll"))
        form = PollGlobalForm(request.POST, request.FILES, instance=poll)

        if form.is_valid():
            form.save(request.user)
            messages.success(request, _("Survey edited with success!"))
            return redirect(reverse("polls_global.poll_list"))
        else:
            context = self.get_context_data()
            context["form"] = form
            messages.error(request, form.non_field_errors())
            messages.error(request, _("Sorry, you did not complete the registration."))
            return render(request, self.template_name, context)
