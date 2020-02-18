from django import forms
from django.utils.translation import gettext as _
from dash.orgs.models import Org, OrgBackend

from .models import PollGlobal
from ureport.backend.rapidpro import RapidProBackendGlobal


class PollGlobalForm(forms.ModelForm):
    flow_uuid = forms.ChoiceField(
        label=_("Select a flow on RapidPro that will shape your global survey"), help_text=_(
            "Select a flow on RapidPro that will shape your global survey"), required=True, choices=[]
    )

    title = forms.CharField(
        max_length=255, widget=forms.TextInput(attrs={"placeholder": _(
            "Insert the survey name"), "class": "input"})
    )

    poll_date = forms.DateField(
        label=_("Start Date"),
        required=True,
        widget=forms.DateInput(
            attrs={"placeholder": _("Please set the date"), "class": "input", "autocomplete": "off"}),
    )

    poll_end_date = forms.DateField(
        label=_("End Date"),
        required=False,
        widget=forms.DateInput(attrs={"placeholder": _(
            "The date this survey was finished"), "class": "input", "autocomplete": "off"}),
    )

    is_active = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "is-checkradio"}))

    description = forms.CharField(
        label=_("Description"),
        required=True,
        widget=forms.Textarea(
            attrs={"placeholder": _("Survey Description"), "required": True, "class": "textarea", "rows": 5}
        ),
    )

    class Meta:
        fields = ["flow_uuid", "title", "poll_date", "poll_end_date", "is_active", "description"]
        model = PollGlobal

    def __init__(self, *args, **kwargs):
        super(PollGlobalForm, self).__init__(*args, **kwargs)

        rapidpro_workspace_global = RapidProBackendGlobal()
        flows = rapidpro_workspace_global.format_all_flows_structure()
        self.fields["flow_uuid"].choices = [
            (f["uuid"], f["name"] + " (" + f.get("date_hint", "--") + ")")
            for f in sorted(flows.values(), key=lambda k: k["name"].lower().strip())
        ]

    def save(self, user):
        instance = super().save(commit=False)
        instance.created_by = user
        instance.modified_by = user
        instance.save()
