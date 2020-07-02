from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext as _

from smartmin.views import SmartTemplateView
from rtm.utils import get_paginator
from rtm.polls.models import Poll

from .models import PollGlobal, PollGlobalSurveys
from .forms import PollGlobalForm


class ListView(SmartTemplateView):
    template_name = "polls_global/index.html"
    permission = "polls_global.poll_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("query", "")
        sort_field = self.request.GET.get("sort")
        sort_direction = self.request.GET.get("dir")
        page = self.request.GET.get("page")

        filters = {}
        sortered = "-is_active"

        if query:
            filters["title__icontains"] = query

        if sort_field:
            sortered = "{}{}".format("-" if sort_direction == "desc" else "", sort_field)

        context["polls"] = get_paginator(
            PollGlobal.objects.filter(**filters).order_by("{}".format(sortered), "-created_on"), page
        )
        context["query"] = query
        return context


class CreateView(SmartTemplateView):
    template_name = "polls_global/form.html"
    permission = "polls_global.poll_create"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = PollGlobalForm()
        context["page_subtitle"] = _("New")
        return context

    def post(self, request, *args, **kwargs):
        form = PollGlobalForm(request.POST, request.FILES)

        if form.is_valid():
            cleaned_data = form.cleaned_data
            instance_poll_global = form.save(request.user)
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
    permission = "polls_global.poll_update"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        poll = get_object_or_404(PollGlobal, pk=self.kwargs.get("poll"))

        data = {
            "title": poll.title,
            "poll_date": poll.poll_date,
            "poll_end_date": poll.poll_end_date,
            "is_active": poll.is_active,
            "description": poll.description,
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


class GrantView(SmartTemplateView):
    template_name = "polls_global/grant_list.html"
    permission = "polls_global.poll_grant"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        poll = get_object_or_404(PollGlobal, pk=self.kwargs.get("poll"))

        context["polls_pending"] = PollGlobalSurveys.objects.filter(poll_global=poll, is_joined=False).order_by("-pk")
        context["polls_accepted"] = PollGlobalSurveys.objects.filter(poll_global=poll, is_joined=True).order_by("-pk")
        return context


class GrantUpdateView(SmartTemplateView):
    template_name = "polls_global/grant_list.html"
    permission = "polls_global.poll_grant"

    def get(self, request, *args, **kwargs):
        super().get_context_data(**kwargs)
        poll_global = get_object_or_404(PollGlobal, pk=self.kwargs.get("poll"))
        poll_local = get_object_or_404(Poll, pk=self.kwargs.get("survey"))
        global_survey = PollGlobalSurveys.objects.filter(poll_global=poll_global, poll_local=poll_local).first()
        action = self.request.GET.get("action")

        if global_survey and action:
            if action == "approve":
                global_survey.is_joined = True
                global_survey.save()
            elif action == "remove":
                global_survey.delete()

        return redirect(self.request.META.get("HTTP_REFERER"))
