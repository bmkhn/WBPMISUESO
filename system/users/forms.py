from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from django.core.exceptions import ValidationError

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))


class FacultyRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = [
            'given_name', 'middle_initial', 'last_name', 'sex', 'email', 'contact_no',
            'campus', 'college', 'role', 'degree', 'expertise', 'password', 'confirm_password'
        ]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

    # def clean_valid_id(self):
    #     valid_id = self.cleaned_data.get("valid_id")
    #     if not valid_id:
    #         raise ValidationError("Please upload a valid ID image.")
    #     return valid_id