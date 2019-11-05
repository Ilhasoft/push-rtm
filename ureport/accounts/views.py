from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext as _
from django.db.models import Q
from django.contrib.auth import get_user_model

from dash.orgs.models import Org
from dash.orgs.views import OrgObjPermsMixin, OrgPermsMixin
from smartmin.views import SmartTemplateView
from ureport.utils import get_paginator, log_save

from .forms import AccountForm, GlobalAccountForm


class ListView(OrgObjPermsMixin, SmartTemplateView):
    template_name = "accounts/index.html"
    permission = "orgs.org_manage_accounts"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("query", "")
        sort_field = self.request.GET.get("sort")
        sort_direction = self.request.GET.get("dir")
        page = self.request.GET.get("page")
        org = kwargs.get("org", None)

        filters = {}
        sortered = "first_name"

        if query:
            filters["first_name__icontains"] = query

        if sort_field:
            sortered = "{}{}".format("-" if sort_direction == "desc" else "", sort_field)

        queryset = (
            get_user_model()
            .objects.all()
            .exclude(is_staff=True)
            .exclude(is_superuser=True)
            .exclude(password=None)
            .exclude(email__exact="")
        )

        if not self.request.user.is_superuser:
            org = self.request.org

        queryset = queryset.filter(
            Q(org_admins=org) | Q(org_editors=org) | Q(org_viewers=org)
        )

        context["users"] = get_paginator(queryset.filter(**filters, is_active=True).order_by(sortered), page)

        context["query"] = query
        context["org"] = org
        return context


class CreateView(OrgObjPermsMixin, SmartTemplateView):
    template_name = "accounts/form.html"
    permission = "orgs.org_manage_accounts"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = AccountForm()
        context["page_subtitle"] = _("New")
        return context

    def post(self, request, *args, **kwargs):
        form = form = AccountForm(request.POST)

        if form.is_valid():
            if request.user.is_superuser and kwargs.get("org"):
                self.request.org = Org.objects.get(pk=kwargs.get("org"))
            instance = form.save(self.request)
            messages.success(request, _("User created with success!"))
            log_save(self.request.user, instance, 1)
            if request.user.is_superuser and kwargs.get("org"):
                return redirect(reverse("accounts.user_org_list", args=[self.request.org.id]))
            return redirect(reverse("accounts.user_list"))
        else:
            context = self.get_context_data()
            context["form"] = form
            messages.error(request, _("Sorry, you did not complete the registration."))
            messages.error(request, form.non_field_errors())
            return render(request, self.template_name, context)


class EditView(OrgObjPermsMixin, SmartTemplateView):
    template_name = "accounts/form.html"
    permission = "orgs.org_manage_accounts"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(get_user_model(), pk=self.kwargs["user"])

        data = {
            "username": user.username,
            "first_name": user.first_name,
            "email": user.email,
            "groups": list(user.groups.all().values_list("id", flat=True)),
        }

        context["form"] = AccountForm(initial=data, password_is_required=False)
        context["page_subtitle"] = _("Edit")
        return context

    def post(self, request, *args, **kwargs):
        user = get_object_or_404(get_user_model(), pk=self.kwargs["user"])
        form = AccountForm(request.POST, request.FILES, instance=user, password_is_required=False)

        if form.is_valid():
            if request.user.is_superuser and kwargs.get("org"):
                self.request.org = Org.objects.get(pk=kwargs.get("org"))
            instance = form.save(self.request)
            messages.success(request, _("User edited with success!"))
            log_save(self.request.user, instance, 2)
            if request.user.is_superuser and kwargs.get("org"):
                return redirect(reverse("accounts.user_org_list", args=[self.request.org.id]))
            return redirect(reverse("accounts.user_list"))
        else:
            context = self.get_context_data()
            context["form"] = form
            messages.error(request, _("Sorry, you did not complete the registration."))
            messages.error(request, form.non_field_errors())
            return render(request, self.template_name, context)


class DeleteView(SmartTemplateView):
    template_name = "accounts/info.html"
    permission = "orgs.org_manage_accounts"

    def post(self, request, *args, **kwargs):
        super().get_context_data(**kwargs)
        user = get_user_model().objects.filter(pk=self.kwargs["user"]).first()

        if not user:
            return redirect(self.request.META.get("HTTP_REFERER"))

        if request.user.is_superuser and kwargs.get("org"):
            self.request.org = Org.objects.get(pk=kwargs.get("org"))

        user.is_active = False
        user.save()

        if user in self.request.org.get_org_users():
            self.request.org.administrators.remove(user)
            self.request.org.editors.remove(user)
            self.request.org.viewers.remove(user)

        log_save(self.request.user, user, 3)
        return redirect(self.request.META.get("HTTP_REFERER"))

# global


class GlobalListView(OrgPermsMixin, SmartTemplateView):
    template_name = "accounts/global/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("query", "")
        sort_field = self.request.GET.get("sort")
        sort_direction = self.request.GET.get("dir")
        page = self.request.GET.get("page")

        filters = {}
        sortered = "first_name"

        if query:
            filters["first_name__icontains"] = query

        if sort_field:
            sortered = "{}{}".format("-" if sort_direction == "desc" else "", sort_field)

        queryset = (
            get_user_model()
            .objects.all()
            .filter(is_staff=True)
            .filter(is_superuser=True)
            .exclude(password=None)
            .exclude(email__exact="")
        )

        context["users"] = get_paginator(queryset.filter(**filters, is_active=True).order_by(sortered), page)
        context["query"] = query
        return context


class GlobalCreateView(OrgPermsMixin, SmartTemplateView):
    template_name = "accounts/global/form.html"
    permission = "orgs.org_manage_accounts"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = GlobalAccountForm()
        context["page_subtitle"] = _("New")
        return context

    def post(self, request, *args, **kwargs):
        print(request.POST)
        form = form = GlobalAccountForm(request.POST)

        if form.is_valid():
            if request.user.is_superuser and kwargs.get("org"):
                self.request.org = Org.objects.get(pk=kwargs.get("org"))
            instance = form.save(self.request)
            messages.success(request, _("User created with success!"))
            log_save(self.request.user, instance, 1)
            if request.user.is_superuser and kwargs.get("org"):
                return redirect(reverse("accounts.user_org_list", args=[self.request.org.id]))
            return redirect(reverse("accounts.user_list"))
        else:
            context = self.get_context_data()
            context["form"] = form
            messages.error(request, _("Sorry, you did not complete the registration."))
            messages.error(request, form.non_field_errors())
            return render(request, self.template_name, context)
