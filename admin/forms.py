from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import ugettext_lazy as _

class FullUserForm(UserCreationForm):
    first_name = forms.RegexField(label=_("First Name"), max_length=30, regex=r'^[\w.-]+\s*$',
                                  help_text= _("User's first name."),
                                  error_messages = {'invalid': _("This value may contain only letters, numbers and ./- characters.")})
    last_name = forms.RegexField(label=_("Last Name"), max_length=30, regex=r'^[\w.-]+\s*$',
                                  help_text= _("User's last name."),
                                  error_messages={'invalid': _("This value may contain only letters, numbers and ./- characters.")})
    email = forms.EmailField(label=_("Email Address"), help_text=_("User's email address."),
                             error_messages={'invalid':_("This value must be a valid email address")})
    is_superuser = forms.BooleanField(label=_("Super User"), required=False)

    def save(self, commit=True):
        user = super(FullUserForm, self).save(commit=False)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.email = self.cleaned_data["email"]
        user.is_superuser = self.cleaned_data["is_superuser"]
        if commit:
            user.save()
        return user

class FullUserChangeForm(UserChangeForm):
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput, 
                                required=False)
    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput,
        help_text = _("Enter the same password as above, for verification."), required=False)

    first_name = forms.RegexField(label=_("First Name"), max_length=30, regex=r'^[\w.-]+\s*$',
                                  help_text= _("User's first name."),
                                  error_messages = {'invalid': _("This value may contain only letters, numbers and ./- characters.")})
    last_name = forms.RegexField(label=_("Last Name"), max_length=30, regex=r'^[\w.-]+\s*$',
                                  help_text= _("User's last name."),
                                  error_messages={'invalid': _("This value may contain only letters, numbers and ./- characters.")})
    email = forms.EmailField(label=_("Email Address"), help_text=_("User's email address."),
                             error_messages={'invalid':_("This value must be a valid email address")})
    is_superuser = forms.BooleanField(label=_("Super User"), required=False)

    def save(self, commit=True):
        user = super(FullUserChangeForm, self).save(commit=False)
        new_pw = self.cleaned_data['password1']
        if new_pw.strip():
            user.set_password(new_pw)
        user.first_name = self.cleaned_data['first_name'].strip()
        user.last_name = self.cleaned_data['last_name'].strip()
        user.email = self.cleaned_data['email']
        user.is_superuser = self.cleaned_data['is_superuser']
        if commit:
            user.save()
        return user
        
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "is_superuser",)

class RecordForm(forms.Form):
    full_name = forms.CharField()
    email = forms.EmailField()
    street_address = forms.CharField()
    postal_code = forms.CharField()
    country = forms.CharField(initial='USA')
    phone_number = forms.CharField(required=False)

class AccountForm(forms.Form):
    RADIO_CHOICES = (
        ('owner', "Owner"),
        ('fullShare', "Full Share"),
    )
    full_name = forms.CharField()
    email = forms.EmailField()

