from django import forms
from system.users.models import College
from shared.projects.models import SustainableDevelopmentGoal
from .models import SystemSetting, APIConnection
from rest_framework_api_key.models import APIKey
from system.users.models import College, Campus 

class CampusForm(forms.ModelForm):
    class Meta:
        model = Campus
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Tiniguiban Campus'}),
        }

class CollegeForm(forms.ModelForm):
    class Meta:
        model = College
        fields = ['name', 'campus', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'campus': forms.Select(attrs={'class': 'form-select'}), # This will now be a dropdown of Campus objects
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class SDGForm(forms.ModelForm):
    class Meta:
        model = SustainableDevelopmentGoal
        # Corrected fields based on your models.py
        fields = ['goal_number', 'name']
        widgets = {
            'goal_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 1'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., No Poverty'}),
        }

class SystemSettingForm(forms.ModelForm):
    class Meta:
        model = SystemSetting
        fields = ['value']
        widgets = {
            'value': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
class DeleteAccountForm(forms.Form):
    password = forms.CharField(
        label="Confirm your password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password to confirm'})
    )

class APIConnectionRequestForm(forms.ModelForm):
    """
    Form for users/admins to request a new API connection.
    """
    class Meta:
        model = APIConnection
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Library System'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the purpose of this connection...'}),
        }

class APIKeyForm(forms.ModelForm):
    # Kept for legacy or direct admin creation
    class Meta:
        model = APIKey
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Partner University SIS'}),
        }