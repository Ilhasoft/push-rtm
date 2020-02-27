# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import json
import re
from datetime import timedelta

import six

from dash.categories.models import Category
from dash.orgs.views import OrgObjPermsMixin, OrgPermsMixin
from smartmin.csv_imports.models import ImportTask
from smartmin.views import SmartCreateView, SmartCRUDL, SmartCSVImportView, SmartUpdateView, SmartTemplateView

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.timesince import timesince
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from dash.orgs.models import OrgBackend
from ureport.utils import json_date_to_datetime, get_paginator
from ureport.polls_global.models import PollGlobal, PollGlobalSurveys

from .models import Poll, PollImage, PollQuestion


class PollForm(forms.ModelForm):
    is_active = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "is-checkradio"}))

    title = forms.CharField(
        max_length=255, widget=forms.TextInput(attrs={"placeholder": _("Insert the survey name"), "class": "input"})
    )

    flow_uuid = forms.ChoiceField(
        label=_("Select a flow on RapidPro"),
        help_text=_("Select a flow on RapidPro"),
        choices=[],
        widget=forms.Select(attrs={"id": "flow_uuid"})
    )

    response_content = forms.CharField(
        required=False,
        label=_("Description"),
        help_text=_("Description"),
        widget=forms.Textarea(
            attrs={"placeholder": _(
                "Insert the survey description"), "class": "textarea", "rows": 6}
        ),
    )

    connect_global = forms.BooleanField(
        label=_("Connect to on ongoing global survey"),
        required=False, widget=forms.CheckboxInput(attrs={"class": "is-checkradio"}))

    global_survey = forms.ModelChoiceField(
        required=False,
        empty_label=_("Select a global survey"),
        label=_("Select a global survey"),
        help_text=_("Select a global survey"),
        queryset=PollGlobal.objects.filter(
            Q(poll_end_date__gte=timezone.now()) |
            Q(poll_end_date__isnull=True),
            poll_date__lte=timezone.now(),
            is_active=True,
        )
    )

    percent_compability = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(
            attrs={"id": "percent-compability-hidden"}
        )
    )

    def __init__(self, *args, **kwargs):
        self.org = kwargs["org"]
        del kwargs["org"]
        self.backend = kwargs["backend"]
        del kwargs["backend"]

        super(PollForm, self).__init__(*args, **kwargs)

        instance_form = kwargs.get("instance")
        if instance_form:
            self.fields["flow_uuid"].widget = forms.HiddenInput(attrs={"id": "flow_uuid"})
            self.fields["flow_uuid"].choices = [(instance_form.flow_uuid, instance_form.flow_uuid)]
        else:
            flows = self.org.get_flows(self.backend)
            self.fields["flow_uuid"].choices = [
                (f["uuid"], f["name"] + " (" + f.get("date_hint", "--") + ")")
                for f in sorted(flows.values(), key=lambda k: k["name"].lower().strip())
            ]

    def clean(self):
        cleaned_data = self.cleaned_data

        if not self.org.backends.filter(is_active=True).exists():
            raise ValidationError(
                _("Your org does not have any API token configuration."))

        cleaned_data["category"] = Category.objects.get(org=self.org)

        return cleaned_data

    class Meta:
        model = Poll
        fields = ("is_active", "backend", "title",
                  "flow_uuid", "category", "response_content")


class PollResponseForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.org = kwargs["org"]
        del kwargs["org"]
        super(PollResponseForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Poll
        fields = ("response_title", "response_author", "response_content")


class PollFlowForm(forms.ModelForm):
    poll_date = forms.DateTimeField(
        label=_("Start Date"),
        required=False,
        widget=forms.DateTimeInput(
            attrs={"placeholder": _("Please set the date"), "class": "input"}),
    )

    poll_end_date = forms.DateTimeField(
        label=_("End Date"),
        required=False,
        widget=forms.DateTimeInput(attrs={"placeholder": _(
            "The date this survey was finished"), "class": "input"}),
    )

    def __init__(self, *args, **kwargs):
        self.org = kwargs["org"]
        del kwargs["org"]
        self.flow = kwargs["flow"]
        del kwargs["flow"]

        super(PollFlowForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = self.cleaned_data
        poll_date = cleaned_data.get("poll_date")
        poll_end_date = cleaned_data.get("poll_end_date")

        flows = self.org.get_flows(self.flow.backend)
        flow = flows.get(self.flow.flow_uuid)

        if not poll_date and flow:
            date = flow.get("created_on", None)
            if date:
                poll_date = json_date_to_datetime(date)

        if not poll_date:
            poll_date = timezone.now()

        cleaned_data["poll_date"] = poll_date
        cleaned_data["poll_end_date"] = poll_end_date
        return cleaned_data

    class Meta:
        model = Poll
        fields = ("poll_date", "poll_end_date")


class QuestionForm(ModelForm):
    """
    Validates that all included questions have titles.
    """

    def clean(self):
        cleaned = self.cleaned_data
        included_count = 0

        # look at all our included polls
        for key in cleaned.keys():
            match = re.match(r"ruleset_([\w\-]+)_include", key)

            # this field is being included
            if match and cleaned[key]:
                # get the title for it
                title_key = "ruleset_%s_title" % match.group(1)
                if not cleaned[title_key]:
                    raise ValidationError(
                        _("You must include a title for every included question."))

                if len(cleaned[title_key]) > 255:
                    raise ValidationError(
                        _("Title too long. The max limit is 255 characters for each title"))

                included_count += 1

        if not included_count:
            raise ValidationError(
                _("You must include at least one poll question."))

        return cleaned

    class Meta:
        model = Poll
        fields = ("id",)


class PollCRUDL(SmartCRUDL):
    model = Poll
    actions = (
        "create",
        "list",
        "update",
        "questions",
        "images",
        "responses",
        "pull_refresh",
        "import",
        "poll_date",
        "poll_flow",
    )

    class PollDate(OrgObjPermsMixin, SmartUpdateView):
        form_class = PollFlowForm
        title = _("Adjust poll date")
        success_url = "id@polls.poll_questions"
        fields = ("poll_date", "poll_end_date")
        default_template = "polls/form_date.html"
        success_message = _(
            "Your survey has been updated, now pick which questions to include.")

        def get_form_kwargs(self):
            kwargs = super(PollCRUDL.PollDate, self).get_form_kwargs()
            kwargs["org"] = self.request.org
            kwargs["flow"] = self.object
            return kwargs

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context["page_subtitle"] = _(self.request.session.get("action_save", "Edit"))
            return context

    class PollFlow(OrgObjPermsMixin, SmartUpdateView):
        form_class = PollFlowForm
        title = _("Configure flow")
        success_url = "id@polls.poll_poll_date"
        fields = ("flow_uuid",)
        success_message = _(
            "Your survey has been configured, now adjust the poll date.")

        def get_form_kwargs(self):
            kwargs = super(PollCRUDL.PollFlow, self).get_form_kwargs()
            kwargs["org"] = self.request.org
            kwargs["backend"] = self.object.backend
            return kwargs

        def pre_process(self, request, *args, **kwargs):
            obj = self.get_object()
            if obj.flow_uuid:
                return HttpResponseRedirect(reverse("polls.poll_poll_date", args=[obj.pk]))
            return None

        def pre_save(self, obj):
            obj = super(PollCRUDL.PollFlow, self).pre_save(obj)
            obj.org = self.request.org

            now = timezone.now()
            five_minutes_ago = now - timedelta(minutes=5)

            similar_poll = Poll.objects.filter(
                org=obj.org,
                flow_uuid=obj.flow_uuid,
                backend=obj.backend,
                is_active=True,
                created_on__gte=five_minutes_ago,
            ).first()
            if similar_poll:
                obj = similar_poll

            flow = obj.get_flow()

            date = flow.get("created_on", None)
            if date:
                flow_date = json_date_to_datetime(date)
            else:
                flow_date = timezone.now()

            obj.poll_date = flow_date
            return obj

        def post_save(self, obj):
            obj = super(PollCRUDL.PollFlow, self).post_save(obj)
            obj.update_or_create_questions(user=self.request.user)

            Poll.pull_poll_results_task(obj)
            return obj

    class Create(OrgPermsMixin, SmartCreateView):
        form_class = PollForm
        success_url = "id@polls.poll_poll_date"
        permission = "polls.poll_create"
        default_template = "polls/form.html"
        fields = ("title", "flow_uuid", "response_content",
                  "connect_global", "global_survey", "percent_compability")
        success_message = _(
            "Your survey has been created, now adjust the poll date.")
        title = _("Create Survey")

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context["page_subtitle"] = _("New")
            context["global_survey"] = PollGlobal.objects.filter(
                is_active=True,
                poll_date__lte=timezone.now(),
                poll_end_date__gte=timezone.now(),
            )
            context["show_connect_global"] = True
            return context

        def get_form_kwargs(self):
            kwargs = super(PollCRUDL.Create, self).get_form_kwargs()
            kwargs["org"] = self.request.org
            kwargs["backend"] = self.request.org.backends.filter(
                is_active=True).first()

            try:
                Category.objects.get(org=self.org)
            except Category.DoesNotExist:
                Category.objects.create(
                    name="default",
                    org=self.org,
                    created_by_id=self.request.user.pk,
                    modified_by_id=self.request.user.pk,
                )

            return kwargs

        def pre_save(self, obj):
            obj = super(PollCRUDL.Create, self).pre_save(obj)
            org = self.request.org
            obj.org = org
            obj.backend = org.backends.filter(is_active=True).first()

            now = timezone.now()
            five_minutes_ago = now - timedelta(minutes=5)

            similar_poll = Poll.objects.filter(
                org=obj.org, flow_uuid="", backend=obj.backend, is_active=True, created_on__gte=five_minutes_ago
            ).first()
            if similar_poll:
                obj = similar_poll

            flow = obj.get_flow()

            date = flow.get("created_on", None)
            if date:
                flow_date = json_date_to_datetime(date)
            else:
                flow_date = timezone.now()

            obj.poll_date = flow_date
            return obj

        def post_save(self, obj):
            obj = super(PollCRUDL.Create, self).post_save(obj)
            obj.update_or_create_questions(user=self.request.user)
            Poll.pull_poll_results_task(obj)
            self.request.session["action_save"] = "New"

            if self.form.cleaned_data["connect_global"]:
                PollGlobalSurveys.objects.create(poll_global=self.form.cleaned_data[
                    "global_survey"], poll_local=obj,
                    percent_compability=self.form.cleaned_data["percent_compability"])

            return obj

    class Images(OrgObjPermsMixin, SmartUpdateView):
        success_url = "id@polls.poll_responses"
        title = _("Poll Images")
        success_message = _(
            "Now enter any responses you'd like to feature. (if any)")

        def get_form(self):
            form = super(PollCRUDL.Images, self).get_form()
            form.fields.clear()

            idx = 1

            # add existing images
            for image in self.object.images.all().order_by("pk"):
                image_field_name = "image_%d" % idx
                image_field = forms.ImageField(
                    required=False,
                    initial=image.image,
                    label=_("Image %d") % idx,
                    help_text=_(
                        "Image to display on poll page and in previews. (optional)"),
                )

                self.form.fields[image_field_name] = image_field
                idx += 1

            while idx <= 3:
                self.form.fields["image_%d" % idx] = forms.ImageField(
                    required=False,
                    label=_("Image %d") % idx,
                    help_text=_(
                        "Image to display on poll page and in previews (optional)"),
                )
                idx += 1

            return form

        def post_save(self, obj):
            obj = super(PollCRUDL.Images, self).post_save(obj)

            # remove our existing images
            self.object.images.all().delete()

            # overwrite our new ones
            # TODO: this could probably be done more elegantly
            for idx in range(1, 4):
                image = self.form.cleaned_data.get("image_%d" % idx, None)

                if image:
                    PollImage.objects.create(
                        poll=self.object, image=image, created_by=self.request.user, modified_by=self.request.user
                    )

            return obj

    class Responses(OrgObjPermsMixin, SmartUpdateView):
        form_class = PollResponseForm
        title = _("Poll Response")
        success_url = "@polls.poll_list"
        success_message = _("Your poll has been updated.")
        fields = ("response_title", "response_author", "response_content")

        def get_form_kwargs(self):
            kwargs = super(PollCRUDL.Responses, self).get_form_kwargs()
            kwargs["org"] = self.request.org
            return kwargs

    class Questions(OrgObjPermsMixin, SmartUpdateView):
        success_url = "@polls.poll_list"
        title = _("Poll Questions")
        form_class = QuestionForm
        success_message = _("Your survey has been updated.")
        default_template = "polls/form_questions.html"

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context["page_subtitle"] = _(self.request.session.get("action_save", "Edit"))
            return context

        def derive_fields(self):
            questions = self.object.questions.all()

            fields = []
            for question in questions:
                fields.append("ruleset_%s_label" % question.ruleset_uuid)
                fields.append("ruleset_%s_title" % question.ruleset_uuid)
                fields.append("ruleset_%s_send_messages" % question.ruleset_uuid)
                fields.append("ruleset_%s_include" % question.ruleset_uuid)
                fields.append("ruleset_%s_sdgs" % question.ruleset_uuid)

            return fields

        def get_questions(self):
            return self.object.questions.all().order_by("-priority", "pk")

        def get_flow_definition(self):
            temba_client = self.request.org.get_temba_client()
            definitions = temba_client.get_definitions(flows=self.object.flow_uuid)
            flow_definitions = definitions.flows

            return flow_definitions

        def get_send_messages(self):
            flows = self.get_flow_definition()

            send_msgs = []
            nodes = []
            action_sets = []
            for flow in flows:
                nodes_flow = flow.get("nodes", [])
                for node in nodes_flow:
                    nodes.append(node)

                action_sets_flow = flow.get("action_sets", [])
                for action_set in action_sets_flow:
                    action_sets.append(action_set)

            for node in nodes:
                actions = node.get("actions")

                for action in actions:
                    text = action.get("text")
                    if text:
                        send_msgs.append(text)

            for action_set in action_sets:
                actions = action_set.get("actions")

                for action in actions:
                    msg = action.get("msg")
                    if msg:
                        text = msg.values()
                        send_msgs.append(list(text)[0])

            if not send_msgs:
                send_msgs = ""

            return list(set(send_msgs))

        def get_form(self):
            form = super(PollCRUDL.Questions, self).get_form()
            form.fields.clear()

            # fetch this single flow so we load what rules are available
            questions = self.get_questions()

            initial = self.derive_initial()
            counter = 1

            for question in questions:
                include_field_name = "ruleset_%s_include" % question.ruleset_uuid
                include_field_initial = initial.get(include_field_name, True)
                include_field = forms.BooleanField(
                    label=_("Allow display of survey results"),
                    required=False,
                    initial=include_field_initial,
                    help_text=_(
                        "Whether to include this question in your public results"),
                    widget=forms.CheckboxInput(
                        attrs={"class": "is-checkradio"}),
                )

                label_field_name = "ruleset_%s_label" % question.ruleset_uuid
                label_field_initial = initial.get(label_field_name, "")
                label_field = forms.CharField(
                    label=counter,
                    widget=forms.HiddenInput(
                        attrs={"readonly": "readonly", "class": "input"}),
                    required=False,
                    initial=label_field_initial,
                    help_text=_("The label of the ruleset from RapidPro"),
                )

                title_field_name = "ruleset_%s_title" % question.ruleset_uuid
                title_field_initial = initial.get(title_field_name, "")
                title_field = forms.CharField(
                    label=_("Question"),
                    disabled=True,
                    widget=forms.Textarea(
                        attrs={
                            "class": "textarea",
                            "rows": 2,
                            "placeholder": _("Put a title here for your question"),
                        }
                    ),
                    required=False,
                    initial=title_field_initial,
                    help_text=_(
                        "The question posed to your audience, will be displayed publicly"),
                )

                send_messages_field_name = "ruleset_%s_send_messages" % question.ruleset_uuid

                send_messages_choices = []
                send_messages_list = initial.get(send_messages_field_name, "")
                for send_message in send_messages_list:
                    send_messages_choices.append((send_message, send_message))

                send_messages_choices = tuple(send_messages_choices)

                send_messages_field = forms.MultipleChoiceField(
                    label=_("Send Messages"),
                    choices=send_messages_choices,
                    required=False,
                    widget=forms.CheckboxSelectMultiple(
                        attrs={
                            "class": "form-control send-message",
                        }
                    ),
                )

                sdgs_field_name = "ruleset_%s_sdgs" % question.ruleset_uuid
                sdgs_field_initial = initial.get(sdgs_field_name, "")
                sdgs_field = forms.MultipleChoiceField(
                    label=_("SDGs"),
                    choices=settings.SDG_LIST,
                    initial=sdgs_field_initial,
                    required=False,
                    widget=forms.SelectMultiple(
                        attrs={
                            "multiple": True,
                            "class": "chosen-select form-control sdgs-select",
                            "data": "chosen-select",
                            "data-placeholder": _("Select one or more Tags."),
                        }
                    ),
                )

                counter += 1
                self.form.fields[label_field_name] = label_field
                self.form.fields[send_messages_field_name] = send_messages_field
                self.form.fields[title_field_name] = title_field
                self.form.fields[sdgs_field_name] = sdgs_field
                self.form.fields[include_field_name] = include_field

            return self.form

        def save(self, obj):
            data = self.form.cleaned_data
            poll = self.object
            questions = self.get_questions()

            # for each question
            for question in questions:
                r_uuid = question.ruleset_uuid

                included = data.get("ruleset_%s_include" % r_uuid, False)

                title = data["ruleset_%s_title" % r_uuid]
                sdgs = data["ruleset_%s_sdgs" % r_uuid]

                PollQuestion.objects.filter(poll=poll, ruleset_uuid=r_uuid).update(
                    is_active=included, title=title, priority=0, sdgs=sdgs
                )

            return self.object

        def post_save(self, obj):
            obj = super(PollCRUDL.Questions, self).post_save(obj)

            # clear our cache of featured polls
            Poll.clear_brick_polls_cache(obj.org)

            return obj

        def derive_initial(self):
            initial = dict()
            questions = self.get_questions()
            send_messages = self.get_send_messages()

            for question in questions:
                initial["ruleset_%s_include" %
                        question.ruleset_uuid] = question.is_active
                initial["ruleset_%s_label" %
                        question.ruleset_uuid] = question.ruleset_label
                initial["ruleset_%s_title" %
                        question.ruleset_uuid] = question.title
                initial["ruleset_%s_send_messages" %
                        question.ruleset_uuid] = send_messages
                initial["ruleset_%s_sdgs" %
                        question.ruleset_uuid] = question.sdgs

            return initial

    class List(OrgPermsMixin, SmartTemplateView):
        fields = ("title", "poll_date", "category", "questions",
                  "opinion_response", "sync_status", "created_on")
        default_order = ("-created_on", "id")
        default_template = "polls/index.html"
        permissions = "polls.poll_list"

        def derive_url_pattern(path, action):
            return "^poll/list/"

        def get_queryset(self):
            queryset = super(PollCRUDL.List, self).get_queryset().filter(
                org=self.request.org)
            return queryset

        def get_sync_status(self, obj):
            if obj.has_synced:
                last_synced = cache.get(Poll.POLL_RESULTS_LAST_SYNC_TIME_CACHE_KEY % (
                    obj.org.pk, obj.flow_uuid), None)
                if last_synced:
                    return "Last synced %s ago" % timesince(json_date_to_datetime(last_synced))

                # we know we synced do not check the the progress since that is
                # slow
                return "Synced 100%"

            sync_progress = obj.get_sync_progress()
            return "Syncing... {0:.1f}%".format(sync_progress)

        def get_questions(self, obj):
            return obj.get_questions().count()

        def get_images(self, obj):
            return obj.get_images().count()

        def get_opinion_response(self, obj):
            return obj.response_title or "--"

        def get_category(self, obj):
            return obj.category.name

        def lookup_field_link(self, context, field, obj):
            if field == "questions":
                return reverse("polls.poll_questions", args=[obj.pk])
            elif field == "poll_date":
                return reverse("polls.poll_poll_date", args=[obj.pk])
            elif field == "images":
                return reverse("polls.poll_images", args=[obj.pk])
            elif field == "opinion_response":
                return reverse("polls.poll_responses", args=[obj.pk])
            else:
                return super(PollCRUDL.List, self).lookup_field_link(context, field, obj)

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
                sortered = "{}{}".format(
                    "-" if sort_direction == "desc" else "", sort_field)

            polls = Poll.objects.filter(**filters, org=self.request.org)
            context["query"] = query
            context["polls"] = get_paginator(polls.order_by(sortered), page)
            return context

    class Update(OrgObjPermsMixin, SmartUpdateView):
        form_class = PollForm
        fields = ("is_active", "flow_uuid", "title", "response_content",
                  "connect_global", "global_survey", "percent_compability")
        success_url = "id@polls.poll_poll_date"
        default_template = "polls/form.html"
        success_message = _(
            "Your survey has been updated, now adjust the poll date.")

        def derive_title(self):
            obj = self.get_object()
            flows = obj.org.get_flows(obj.backend)

            flow = flows.get(obj.flow_uuid, dict())

            flow_name = flow.get("name", "")
            flow_date_hint = flow.get("date_hint", "")

            return "Edit Poll for flow [%s (%s)]" % (flow_name, flow_date_hint)

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context["page_subtitle"] = _("Edit")
            context["global_survey"] = PollGlobal.objects.filter(
                is_active=True,
                poll_date__lte=timezone.now(),
                poll_end_date__gte=timezone.now(),
            )
            in_global = PollGlobalSurveys.objects.filter(poll_local=self.object).first()
            context["approve_pending"] = in_global
            context["show_connect_global"] = False
            if not in_global or in_global.is_joined is False:
                context["show_connect_global"] = True
            return context

        def get_form_kwargs(self):
            kwargs = super(PollCRUDL.Update, self).get_form_kwargs()
            kwargs["org"] = self.request.org
            kwargs["backend"] = self.request.org.backends.filter(
                is_active=True).first()
            return kwargs

        def post_save(self, obj):
            obj = super(PollCRUDL.Update, self).post_save(obj)
            obj.update_or_create_questions(user=self.request.user)
            self.request.session["action_save"] = "Edit"
            if self.form.cleaned_data["connect_global"]:
                try:
                    global_survey = PollGlobalSurveys.objects.get(poll_local=self.object)
                    global_survey.poll_global = self.form.cleaned_data["global_survey"]
                    global_survey.percent_compability = self.form.cleaned_data["percent_compability"]
                    global_survey.save()
                except PollGlobalSurveys.DoesNotExist:
                    PollGlobalSurveys.objects.create(poll_global=self.form.cleaned_data[
                        "global_survey"], poll_local=obj,
                        percent_compability=self.form.cleaned_data["percent_compability"])
            else:
                global_survey = PollGlobalSurveys.objects.filter(poll_local=self.object).first()
                if global_survey and not global_survey.is_joined:
                    global_survey.delete()
            return obj

    class PullRefresh(SmartUpdateView):
        fields = ("id",)
        success_url = "@polls.poll_list"
        success_message = None

        def post_save(self, obj):
            poll = self.get_object()
            poll.pull_refresh_task()
            self.success_message = _("Scheduled a pull refresh for poll #%(poll_id)d on org #%(org_id)d") % dict(
                poll_id=poll.pk, org_id=poll.org_id
            )

    class Import(SmartCSVImportView):

        class ImportForm(forms.ModelForm):

            def __init__(self, *args, **kwargs):
                self.org = kwargs["org"]
                del kwargs["org"]
                super(PollCRUDL.Import.ImportForm,
                      self).__init__(*args, **kwargs)

            class Meta:
                model = ImportTask
                fields = "__all__"

        form_class = ImportForm
        model = ImportTask
        fields = ("csv_file",)
        success_message = ""

        def post_save(self, task):
            # configure import params with current org and timezone
            org = self.request.org
            params = dict(
                org_id=org.id,
                timezone=six.text_type(org.timezone),
                original_filename=self.form.cleaned_data["csv_file"].name,
            )
            params_dump = json.dumps(params)
            ImportTask.objects.filter(pk=task.pk).update(
                import_params=params_dump)

            # start the task
            task.start()

            return task

        def get_form_kwargs(self):
            kwargs = super(PollCRUDL.Import, self).get_form_kwargs()
            kwargs["org"] = self.request.org
            return kwargs


class FlowDataView(View):
    def get_percent_compatibility(self, id_global_survey, local_flow_uuid):
        """Get a global flow and a local flow and return the compatibility percentage between both."""
        amount_local_flow_uuids = 0
        amount_global_flow_uuids = 0
        org_local = self.request.org

        try:
            global_survey = PollGlobal.objects.get(pk=id_global_survey)
            global_flow = global_survey.get_flow().get("results", None)
            global_flow_uuids = [question.get("node_uuids") for question in global_flow]

            backend = OrgBackend.objects.get(pk=1)
            local_flow = org_local.get_flows(backend=backend).get(local_flow_uuid).get("results", None)
            local_flow_uuids = [local_question.get("node_uuids") for local_question in local_flow if
                                local_question.get("node_uuids") in global_flow_uuids]

            amount_global_flow_uuids = len(global_flow_uuids)
            amount_local_flow_uuids = len(local_flow_uuids)

            percent_compatibility = ((amount_local_flow_uuids * 100) / amount_global_flow_uuids)

        except ZeroDivisionError:
            percent_compatibility = 0
        except Exception:
            percent_compatibility = None

        return {
            "percent_compatibility": percent_compatibility,
            "amount_global_flow_uuids": amount_global_flow_uuids,
            "amount_local_flow_uuids": amount_local_flow_uuids
        }

    def get(self, request, *args, **kwargs):
        global_survey = self.kwargs["global_survey"]
        local_flow_uuid = self.kwargs["flow_uuid"]

        percent_compatibility = self.get_percent_compatibility(global_survey, local_flow_uuid)
        status_code = 200 if percent_compatibility is not None else 500

        return JsonResponse(percent_compatibility, status=status_code)
