from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.translation import gettext as _

from smartmin.users.models import is_password_complex


class AccountForm(forms.ModelForm):

    username = forms.CharField(
        label=_("Username"),
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            "placeholder": _("username"),
            "required": False,
            "class": "input",
            "readonly": True,
        }),
    )

    first_name = forms.CharField(
        label=_("Name"),
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            "placeholder": _("Name"),
            "required": False,
            "class": "input",
            "readonly": True,
        }),
    )

    new_password = forms.CharField(
        label=_("Password"),
        required=False,
        max_length=255,
        strip=False,
        widget=forms.PasswordInput(attrs={
            "placeholder": _("Password"),
            "class": "input",
        }),
    )

    email = forms.EmailField(
        label=_("E-mail"),
        required=False,
        max_length=255,
        widget=forms.EmailInput(attrs={
            "placeholder": _("Email"),
            "required": False,
            "class": "input",
            "readonly": True,
        }),
    )

    groups = forms.ModelChoiceField(
        widget=forms.RadioSelect,
        queryset=Group.objects.filter(name__in=["Administrators", "Viewers"]),
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
        fields = ["groups"]
        model = get_user_model()


class GlobalAccountForm(forms.ModelForm):

    username = forms.CharField(
        label=_("Username"),
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            "placeholder": _("username"),
            "required": False,
            "class": "input",
            "readonly": True,
        }),
    )

    first_name = forms.CharField(
        label=_("Name"),
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            "placeholder": _("Name"),
            "required": False,
            "class": "input",
            "readonly": True,
        }),
    )

    new_password = forms.CharField(
        label=_("Password"),
        required=False,
        max_length=255,
        strip=False,
        widget=forms.PasswordInput(attrs={
            "placeholder": _("Password"),
            "class": "input",
        }),
    )

    email = forms.EmailField(
        label=_("E-mail"),
        required=False,
        max_length=255,
        widget=forms.EmailInput(attrs={
            "placeholder": _("Email"),
            "required": False,
            "class": "input",
            "readonly": True,
        }),
    )

    groups = forms.ChoiceField(
        widget=forms.RadioSelect, choices=[(1, "Global Admin"), (2, "Global Viewer")], required=True
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

        group = int(self.cleaned_data.get("groups"))
        if group == 1:
            instance.is_superuser = True
            instance.save()
        if group == 2:
            instance.is_superuser = False
            group = Group.objects.get(name="Global Viewers")
            instance.groups.add(group)
            instance.save()

        return instance

    class Meta:
        fields = []
        model = get_user_model()
