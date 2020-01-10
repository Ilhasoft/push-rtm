from django import forms
from django.utils.translation import gettext as _

from .models import PollGlobal


class PollGlobalForm(forms.ModelForm):
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
        fields = ["title", "poll_date", "poll_end_date", "is_active", "description"]
        model = PollGlobal

    def save(self, user):
        instance = super().save(commit=False)
        instance.created_by = user
        instance.modified_by = user
        instance.save()
