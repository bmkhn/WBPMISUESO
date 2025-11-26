from django import forms
from system.users.models import College, Campus 
from shared.projects.models import SustainableDevelopmentGoal
from .models import SystemSetting, APIConnection
from rest_framework_api_key.models import APIKey

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
            'campus': forms.Select(attrs={'class': 'form-select'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class SDGForm(forms.ModelForm):
    class Meta:
        model = SustainableDevelopmentGoal
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
    Includes a Tier selection checklist.
    """
    class Meta:
        model = APIConnection
        fields = ['name', 'description', 'tier']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Library System'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the purpose of this connection...'}),
            'tier': forms.RadioSelect(attrs={'class': 'list-unstyled', 'style': 'list-style-type: none; padding-left: 0;'}),
        }
        help_texts = {
            'tier': 'Select the level of access you require.'
        }

class APIRejectionForm(forms.ModelForm):
    """
    Form for entering a rejection reason.
    """
    class Meta:
        model = APIConnection
        fields = ['rejection_reason']
        widgets = {
            'rejection_reason': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Please provide a reason for rejecting this request.'
            }),
        }
        labels = {
            'rejection_reason': 'Reason for Rejection'
        }

class APIKeyForm(forms.ModelForm):
    class Meta:
        model = APIKey
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Partner University SIS'}),
        }