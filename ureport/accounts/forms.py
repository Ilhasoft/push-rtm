from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.translation import gettext as _

from smartmin.users.models import is_password_complex


class AccountForm(forms.ModelForm):

    username = forms.CharField(
        label=_("Username"),
        required=True,
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("username"), "required": True, "class": "input"}),
    )

    first_name = forms.CharField(
        label=_("Name"),
        required=True,
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("Name"), "required": True, "class": "input"}),
    )

    new_password = forms.CharField(
        label=_("Password"),
        required=True,
        max_length=255,
        strip=False,
        widget=forms.PasswordInput(attrs={"placeholder": _("Password"), "class": "input"}),
    )

    email = forms.EmailField(
        label=_("Groups"),
        required=True,
        max_length=255,
        widget=forms.EmailInput(attrs={"placeholder": _("Email"), "required": True, "class": "input"}),
    )

    groups = forms.ModelChoiceField(
        widget=forms.RadioSelect,
        queryset=Group.objects.all().exclude(name__exact="Global"),
        required=True,
        empty_label=None,
    )

    def __init__(self, *args, **kwargs):
        password_is_required = kwargs.pop("password_is_required", True)
        super().__init__(*args, **kwargs)

        if not password_is_required:
            self.fields["new_password"].required = False
            self.fields["new_password"].label = _("New password")

    def clean_new_password(self):
        password = self.cleaned_data["new_password"]

        if password and not is_password_complex(password):
            raise forms.ValidationError(
                _(
                    "Passwords must have at least 8 characters, including one uppercase, "
                    "one lowercase and one number"
                )
            )

        return password

    def save(self, request):
        instance = super().save(commit=False)
        instance.save()

        new_password = self.cleaned_data["new_password"]
        if new_password:
            instance.set_password(new_password)
            instance.save()

        instance.groups.clear()
        instance.groups.add(self.cleaned_data.get("groups"))
        group = str(self.cleaned_data.get("groups")).lower()

        request.org.administrators.remove(instance)
        request.org.editors.remove(instance)
        request.org.viewers.remove(instance)

        if group == "administrators":
            request.org.administrators.add(instance)
        elif group == "editors":
            request.org.editors.add(instance)
        else:
            request.org.viewers.add(instance)

        return instance

    class Meta:
        fields = ["username", "first_name", "email", "groups"]
        model = get_user_model()
