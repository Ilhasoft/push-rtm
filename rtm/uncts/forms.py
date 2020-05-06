from timezone_field import TimeZoneFormField
from django import forms
from django.conf import settings
from django.utils.translation import gettext as _

from dash.orgs.models import Org
from dash.orgs.models import OrgBackend


class UnctForm(forms.ModelForm):
    name = forms.CharField(
        label=_("Name"),
        required=True,
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("UNCT Name"), "required": True, "class": "input"}),
    )

    host = forms.URLField(
        label=_("RapidPro URL"),
        required=True,
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("RapidPro URL"), "required": True, "class": "input"}),
    )

    api_token = forms.CharField(
        label=_("RapidPro Token"),
        required=True,
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("RapidPro Token"), "required": True, "class": "input"}),
    )

    subdomain = forms.CharField(
        label=_("Slug"),
        required=True,
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("Slug"), "required": True, "class": "input"}),
    )

    language = forms.ChoiceField(required=False, choices=[("", "")] + list(settings.LANGUAGES))
    timezone = TimeZoneFormField()

    # Backend Config
    reporter_group = forms.CharField(
        label=_("Contact Group"),
        help_text=_("The name of the Contact Group that contains registered reporters"),
        required=True,
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("Contact Group"), "required": True, "class": "input"}),
    )

    born_label = forms.CharField(
        label=_("Born Label"),
        help_text=_("The label of the Contact Field that contains the birth date of reporters"),
        required=True,
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("Born Label"), "required": True, "class": "input"}),
    )

    gender_label = forms.CharField(
        label=_("Gender Label"),
        help_text=_("The label of the Contact Field that contains the gender of reporters"),
        required=True,
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("Gender Label"), "required": True, "class": "input"}),
    )

    occupation_label = forms.CharField(
        label=_("Occupation Label"),
        help_text=_("The label of the Contact Field that contains the occupation of reporters"),
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("Occupation Label"), "required": False, "class": "input"}),
    )

    registration_label = forms.CharField(
        label=_("Registration Label"),
        help_text=_("The label of the Contact Field that contains the registration date of reporters"),
        required=True,
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("Registration Label"), "required": True, "class": "input"}),
    )

    state_label = forms.CharField(
        label=_("State Label"),
        help_text=_("The label of the Contact Field that contains the State of reporters"),
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("State Label"), "required": False, "class": "input"}),
    )

    district_label = forms.CharField(
        label=_("District Label"),
        help_text=_("The label of the Contact Field that contains the District of reporters"),
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("District Label"), "required": False, "class": "input"}),
    )

    ward_label = forms.CharField(
        label=_("Ward Label"),
        help_text=_("The label of the Contact Field that contains the Ward of reporters"),
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("Ward Label"), "required": False, "class": "input"}),
    )

    male_label = forms.CharField(
        label=_("Male Label"),
        help_text=_("The label assigned to U-Reporters that are Male."),
        required=True,
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("Male Label"), "required": True, "class": "input"}),
    )

    female_label = forms.CharField(
        label=_("Female Label"),
        help_text=_("The label assigned to U-Reporters that are Female."),
        required=True,
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("Female Label"), "required": True, "class": "input"}),
    )

    def save(self, user):
        instance = super().save(commit=False)
        instance.created_by = user
        instance.modified_by = user
        instance.config = {
            "rapidpro": {
                "born_label": self.cleaned_data.get("born_label"),
                "male_label": self.cleaned_data.get("male_label"),
                "ward_label": self.cleaned_data.get("ward_label"),
                "state_label": self.cleaned_data.get("state_label"),
                "female_label": self.cleaned_data.get("female_label"),
                "gender_label": self.cleaned_data.get("gender_label"),
                "district_label": self.cleaned_data.get("district_label"),
                "reporter_group": self.cleaned_data.get("reporter_group"),
                "occupation_label": self.cleaned_data.get("occupation_label"),
                "registration_label": self.cleaned_data.get("registration_label"),
            }
        }
        instance.save()
        backend = OrgBackend.objects.filter(org=instance).first()

        if backend:
            backend.host = self.cleaned_data.get("host")
            backend.api_token = self.cleaned_data.get("api_token")
            backend.save()
        else:
            OrgBackend.objects.create(
                org=instance,
                backend_type=settings.SITE_BACKEND,
                host=self.cleaned_data.get("host"),
                api_token=self.cleaned_data.get("api_token"),
                slug="rapidpro",
                created_by=instance.created_by,
                modified_by=instance.modified_by,
            )

        return instance

    def clean_domain(self):
        domain = self.cleaned_data["domain"] or ""
        domain = domain.strip().lower()

        if domain:
            if domain == getattr(settings, "HOSTNAME", ""):
                raise forms.ValidationError(_("This domain is used for subdomains"))
            return domain
        else:
            return None

    class Meta:
        fields = ["name", "language", "host", "api_token", "timezone", "subdomain"]
        model = Org
