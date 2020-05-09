from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext as _
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.views.generic import View

from dash.orgs.models import Org
from dash.orgs.views import OrgObjPermsMixin, OrgPermsMixin
from smartmin.views import SmartTemplateView
from rtm.utils import get_paginator

from .forms import AccountForm, GlobalAccountForm
from .models import LogPermissionUser


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

        if self.request.org:
            org = self.request.org
        else:
            org = Org.objects.get(pk=org)

        queryset = queryset.filter(Q(org_admins=org) | Q(org_editors=org) | Q(org_viewers=org))

        log_permission = LogPermissionUser.objects.filter(user__first_name__icontains=query, org=org)

        context["users"] = get_paginator(queryset.filter(**filters, is_active=True).order_by(sortered), page)
        context["log_permission_users"] = log_permission
        context["query"] = query
        context["org"] = org
        context["title"] = org.name
        context["back_to"] = reverse("accounts.user_list")
        return context


class CreateView(OrgObjPermsMixin, SmartTemplateView):
    template_name = "accounts/form.html"
    permission = "orgs.org_manage_accounts"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = AccountForm()
        context["page_subtitle"] = _("New")
        if kwargs.get("org"):
            context["org"] = Org.objects.get(pk=kwargs.get("org"))
        return context

    def post(self, request, *args, **kwargs):
        form = form = AccountForm(request.POST)

        if form.is_valid():
            if request.user.is_superuser and kwargs.get("org"):
                self.request.org = Org.objects.get(pk=kwargs.get("org"))
            instance = form.save(self.request)
            messages.success(request, _("User created with success!"))
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
        if kwargs.get("org"):
            context["org"] = Org.objects.get(pk=kwargs.get("org"))
        return context

    def post(self, request, *args, **kwargs):
        user = get_object_or_404(get_user_model(), pk=self.kwargs["user"])
        form = AccountForm(request.POST, request.FILES, instance=user, password_is_required=False)

        if form.is_valid():
            if request.user.is_superuser and kwargs.get("org"):
                self.request.org = Org.objects.get(pk=kwargs.get("org"))
            instance = form.save(self.request)
            messages.success(request, _("User edited with success!"))
            if request.user.is_superuser and kwargs.get("org"):
                return redirect(reverse("accounts.user_org_list", args=[self.request.org.id]))
            return redirect(reverse("accounts.user_list"))
        else:
            context = self.get_context_data()
            context["form"] = form
            messages.error(request, _("Sorry, you did not complete the registration."))
            messages.error(request, form.non_field_errors())
            return render(request, self.template_name, context)


class DeleteView(OrgObjPermsMixin, View):
    permission = "orgs.org_manage_accounts"

    def post(self, request, *args, **kwargs):
        user = get_user_model().objects.filter(pk=self.kwargs["user"]).first()

        if not user:
            return redirect(self.request.META.get("HTTP_REFERER"))

        if request.user.is_superuser and kwargs.get("org"):
            self.request.org = Org.objects.get(pk=kwargs.get("org"))

        if user in self.request.org.get_org_users():
            group_permission = user.groups.first()
            log = LogPermissionUser.objects.create(user=user, org=self.request.org, permission=group_permission)

            self.request.org.administrators.remove(user)
            self.request.org.editors.remove(user)
            self.request.org.viewers.remove(user)

        return redirect(self.request.META.get("HTTP_REFERER"))


class ActivateView(OrgObjPermsMixin, View):
    permission = "orgs.org_manage_accounts"

    def post(self, request, *args, **kwargs):
        user = get_object_or_404(get_user_model(), pk=self.kwargs["user"])

        if not user:
            return redirect(self.request.META.get("HTTP_REFERER"))

        if request.user.is_superuser and kwargs.get("org"):
            self.request.org = Org.objects.get(pk=kwargs.get("org"))

        group = user.logs_permission_user.filter(org=self.request.org).first()
        group_permission = None
        group_name = ""

        if group:
            group_permission = group.permission
            group_name = group_permission.name if group_permission else None

        if group_name == "Administrators":
            self.request.org.administrators.add(user)
        else:
            self.request.org.viewers.add(user)

        log = user.logs_permission_user.filter(org=self.request.org, permission=group_permission).first()

        if log:
            log.delete()

        return redirect(self.request.META.get("HTTP_REFERER"))


# global


class GlobalListView(OrgPermsMixin, SmartTemplateView):
    template_name = "accounts/global/index.html"
    permission = "orgs.org_manage_accounts"

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_superuser:
            return redirect(reverse("accounts.user_list"))
        return super().get(request)

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
            .filter(
                Q(is_superuser=True)
                | Q(groups__name="Global Viewers")
                | Q(logs_permission_user__permission_id__name="Global Viewers")
            )
            .exclude(password=None)
            .exclude(email__exact="")
        )

        context["users"] = get_paginator(queryset.filter(**filters, is_active=True).order_by(sortered), page)
        context["query"] = query
        context["back_to"] = reverse("accounts.global_list")
        return context


class GlobalCreateView(OrgPermsMixin, SmartTemplateView):
    template_name = "accounts/global/form.html"
    permission = "orgs.org_manage_accounts"

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_superuser:
            return redirect(reverse("accounts.user_list"))
        return super().get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = GlobalAccountForm()
        context["page_subtitle"] = _("New")
        return context

    def post(self, request, *args, **kwargs):
        form = form = GlobalAccountForm(request.POST)

        if form.is_valid():
            form.save(self.request)
            messages.success(request, _("User created with success!"))
            return redirect(reverse("accounts.global_list"))
        else:
            context = self.get_context_data()
            context["form"] = form
            messages.error(request, _("Sorry, you did not complete the registration."))
            messages.error(request, form.non_field_errors())
            return render(request, self.template_name, context)


class GlobalEditView(OrgObjPermsMixin, SmartTemplateView):
    template_name = "accounts/global/form.html"
    permission = "orgs.org_manage_accounts"

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_superuser:
            return redirect(reverse("accounts.user_list"))
        return super().get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(get_user_model(), pk=self.kwargs["user"])

        data = {
            "username": user.username,
            "first_name": user.first_name,
            "email": user.email,
            "groups": "1" if user.is_superuser else "2",
        }

        context["form"] = GlobalAccountForm(initial=data, password_is_required=False)
        context["page_subtitle"] = _("Edit")
        return context

    def post(self, request, *args, **kwargs):
        user = get_object_or_404(get_user_model(), pk=self.kwargs["user"])
        form = GlobalAccountForm(request.POST, request.FILES, instance=user, password_is_required=False)

        if form.is_valid():
            form.save(self.request)
            messages.success(request, _("User edited with success!"))
            return redirect(reverse("accounts.global_list"))
        else:
            context = self.get_context_data()
            context["form"] = form
            messages.error(request, _("Sorry, you did not complete the registration."))
            messages.error(request, form.non_field_errors())
            return render(request, self.template_name, context)


class GlobalDeleteView(OrgObjPermsMixin, View):
    permission = "orgs.org_manage_accounts"

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_superuser:
            return redirect(reverse("accounts.user_list"))
        return super().get(request)

    def post(self, request, *args, **kwargs):
        user = get_object_or_404(get_user_model(), pk=self.kwargs["user"])

        if not user:
            return redirect(self.request.META.get("HTTP_REFERER"))

        if not self.request.user.is_superuser:
            return redirect(reverse("accounts.user_list"))

        group = Group.objects.get(name="Global Viewers")
        if group in user.groups.all():
            user.groups.remove(group)

        log = LogPermissionUser.objects.create(user=user, permission=group)

        return redirect(self.request.META.get("HTTP_REFERER"))


class GlobalActivateView(OrgObjPermsMixin, View):
    permission = "orgs.org_manage_accounts"

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_superuser:
            return redirect(reverse("accounts.user_list"))
        return super().get(request)

    def post(self, request, *args, **kwargs):
        user = get_object_or_404(get_user_model(), pk=self.kwargs["user"])

        if not user:
            return redirect(self.request.META.get("HTTP_REFERER"))

        if not self.request.user.is_superuser:
            return redirect(reverse("accounts.user_list"))

        group = Group.objects.get(name="Global Viewers")
        user.groups.add(group)

        log = LogPermissionUser.objects.filter(user=user, permission=group).first()
        if log:
            log.delete()

        return redirect(self.request.META.get("HTTP_REFERER"))
