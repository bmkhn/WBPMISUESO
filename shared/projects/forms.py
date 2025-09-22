from django import forms
from .models import Project, ProjectDocument, SustainableDevelopmentGoal
from django.contrib.auth import get_user_model

User = get_user_model()


class ProjectForm(forms.ModelForm):
    providers = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'user-details-value'}),
        required=False
    )
    sdgs = forms.ModelMultipleChoiceField(
        queryset=SustainableDevelopmentGoal.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'user-details-value'}),
        required=False
    )
    proposal_document = forms.FileField(required=False)

    class Meta:
        model = Project
        fields = [
            'title', 'project_leader', 'providers', 'agenda', 'campus', 'project_type', 'sdgs',
            'estimated_events', 'estimated_trainees', 'primary_beneficiary', 'primary_location',
            'logistics_type', 'internal_budget', 'external_budget', 'sponsor_name',
            'start_date', 'estimated_end_date', 'proposal_document'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'user-details-value'}),
            'project_leader': forms.Select(attrs={'class': 'user-details-value'}),
            'agenda': forms.TextInput(attrs={'class': 'user-details-value'}),
            'campus': forms.Select(attrs={'class': 'user-details-value'}),
            'project_type': forms.Select(attrs={'class': 'user-details-value'}),
            'estimated_events': forms.NumberInput(attrs={'class': 'user-details-value', 'min': 0}),
            'estimated_trainees': forms.NumberInput(attrs={'class': 'user-details-value', 'min': 0}),
            'primary_beneficiary': forms.TextInput(attrs={'class': 'user-details-value'}),
            'primary_location': forms.TextInput(attrs={'class': 'user-details-value'}),
            'logistics_type': forms.Select(attrs={'class': 'user-details-value'}),
            'internal_budget': forms.NumberInput(attrs={'class': 'user-details-value', 'min': 0, 'step': '0.01'}),
            'external_budget': forms.NumberInput(attrs={'class': 'user-details-value', 'min': 0, 'step': '0.01'}),
            'sponsor_name': forms.TextInput(attrs={'class': 'user-details-value'}),
            'start_date': forms.DateInput(attrs={'class': 'user-details-value', 'type': 'date'}),
            'estimated_end_date': forms.DateInput(attrs={'class': 'user-details-value', 'type': 'date'}),
        }
