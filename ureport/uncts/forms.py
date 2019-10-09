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

    def save(self, user):
        instance = super().save(commit=False)
        instance.created_by = user
        instance.modified_by = user
        instance.config = {"common": {"colors": "", "bg_color": "", "has_jobs": False, "iso_code": "", "is_global": False, "join_text": "", "shortcode": "", "text_font": "", "colors_map": "", "custom_html": "", "dark1_color": "", "dark2_color": "", "dark3_color": "", "ignore_words": "", "light1_color": "", "light2_color": "", "limit_states": "", "headline_font": "", "join_bg_color": "", "join_fg_color": "", "primary_color": "", "has_new_design": False, "twitter_handle": "", "facebook_app_id": "", "secondary_color": "", "text_small_font": "", "whatsapp_number": "", "facebook_page_id": "", "has_extra_gender": False, "facebook_page_url": "", "facebook_pixel_id": "", "google_tracking_id": "", "instagram_username": "", "is_on_landing_page": False, "stories_description": "", "youtube_channel_url": "", "opinions_description": "", "photos_section_title": "", "ureport_announcement": "", "facebook_welcome_text": "", "twitter_search_widget": "", "engagement_description": "", "homepage_join_video_id": "", "is_participation_hidden": False, "instagram_lightwidget_id": "", "engagement_footer_callout": "", "photos_section_description": ""}, "rapidpro": {"born_label": "Born", "male_label": "Male", "ward_label": "", "state_label": "District", "female_label": "Female", "gender_label": "Gender", "district_label": "", "reporter_group": "U-Reporters", "occupation_label": "Occupation", "registration_label": "Registration Date"}}
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
