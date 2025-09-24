from random import randint

from django import forms
from django.conf import settings
from django_recaptcha.fields import ReCaptchaField

from account.models import Accounts


class SignUpForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={"password_toggle": True, "placeholder": "********"}
        ),
        required=True,
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput(
            attrs={"password_toggle": True, "placeholder": "********"},
        ),
        required=True,
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"placeholder": "E-Mail"}),
        required=True,
    )

    if not settings.DEBUG:
        captcha = ReCaptchaField()

    class Meta:
        model = Accounts
        fields = ["email"]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        self.cleaned_data["password"] = password1

        return password2

    def clean_email(self):
        if Accounts.objects.filter(email=self.cleaned_data.get("email")).exists():
            raise forms.ValidationError("An account with this e-mail address exists")

        return self.cleaned_data.get("email")

    @classmethod
    def _generate_confirmation_code(cls):
        return randint(1000, 9999)


class SignInForm(forms.Form):
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"placeholder": "E-Mail"}),
        required=True,
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={"password_toggle": True, "placeholder": "********"}
        ),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        if not Accounts.objects.filter(email=self.cleaned_data.get("email")).exists():
            raise forms.ValidationError(
                f"There is no an account with this e-mail address"
            )

        return self.cleaned_data


class EmailConfirmation(forms.Form):
    confirmation_code = forms.CharField(
        label="Confirmation code",
        widget=forms.TextInput(attrs={"placeholder": "Confirmation code"}),
        required=False,
    )
    account_id = None

    def __init__(self, *args, **kwargs):
        self.account_id = kwargs.pop("account_id", None)
        super().__init__(*args, **kwargs)

    def clean_confirmation_code(self):
        if not Accounts.objects.filter(id=self.account_id).exists():
            raise forms.ValidationError("Account doesn't exists")

        if str(
            Accounts.objects.get(id=self.account_id).confirmation_code
        ) != self.cleaned_data.get("confirmation_code"):
            raise forms.ValidationError("Wrong code")

        return self.cleaned_data
