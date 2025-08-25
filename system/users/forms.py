from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'username', 'given_name', 'middle_initial', 'last_name', 'suffix',
                  'sex', 'contact_no', 'campus', 'college', 'role', 'degree',
                  'expertise', 'company', 'industry', 'is_expert', 'profile_picture']

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))