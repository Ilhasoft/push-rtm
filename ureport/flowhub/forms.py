import json

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from taggit.models import Tag

from .models import Flow


class FlowForm(forms.ModelForm):
    name = forms.CharField(
        label=_("Name"),
        required=True,
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("Flow Name"), "required": True}),
    )

    description = forms.CharField(
        label=_("Description"),
        required=True,
        max_length=255,
        widget=forms.Textarea(
            attrs={"placeholder": _("Flow Description"), "required": True}
        ),
    )

    visible_globally = forms.BooleanField(required=False)

    collected_data = forms.CharField(
        label=_("Collected Data"),
        required=True,
        max_length=255,
        widget=forms.Textarea(
            attrs={"placeholder": _("Collected Data"), "required": True}
        ),
    )

    tags = forms.MultipleChoiceField(
        choices=Tag.objects.all().order_by("name").values_list("name", "name"),
        label=_("Tags"),
        required=True,
        widget=forms.SelectMultiple(
            attrs={
                 "data-placeholder": _("Select one or more Tags."),
            }
        ),
    )

    languages = forms.MultipleChoiceField(
        choices=settings.LANGUAGES,
        label=_("Languages"),
        required=True,
        widget=forms.SelectMultiple(
            attrs={
                "data-placeholder": _("Select one or more Languages."),
            }
        ),
    )

    flow = forms.FileField(widget=forms.FileInput())

    sdgs = forms.MultipleChoiceField(
        label=_("SDG's"), choices=settings.SDG_LIST, widget=forms.CheckboxSelectMultiple(attrs={"required": True})
    )

    class Meta:
        model = Flow
        fields = ['name', 'description', 'collected_data', 'tags', 'sdgs', 'flow', 'visible_globally', 'languages']
    
    def save(self, request):
        instance = super().save(commit=False)
        file_uploaded = self.cleaned_data.get('flow')
        instance.sdgs = self.collected_data('sdgs')

        if file_uploaded:
            with file_uploaded.open():
                instance.flow = json.loads(file_uploaded.read().decode('utf-8'))
        
        instance.created_by = request.user
        instance.modifield_by = request.user
        instance.org = request.org
        instance.save()

        instance.tags.remove(*instance.tags.all())
        if self.collected_data.get('tags'):
            tags = dict([tags for tag in self.collected_data.get('tags')])
            instance.tags.add(tags)
        
        return instance
