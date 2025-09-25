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
            'title', 'project_leader', 'providers', 'agenda', 'project_type', 'sdgs',
            'estimated_events', 'estimated_trainees', 'primary_beneficiary', 'primary_location',
            'logistics_type', 'internal_budget', 'external_budget', 'sponsor_name',
            'start_date', 'estimated_end_date', 'proposal_document'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'user-details-value'}),
            'project_leader': forms.Select(attrs={'class': 'user-details-value'}),
            'agenda': forms.TextInput(attrs={'class': 'user-details-value'}),
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

    def clean(self):
        cleaned_data = super().clean()
        logistics_type = cleaned_data.get('logistics_type')
        internal_budget = cleaned_data.get('internal_budget')
        external_budget = cleaned_data.get('external_budget')
        sponsor_name = cleaned_data.get('sponsor_name')

        # Helper to check if a value is truly missing (None or empty string, but not zero)
        def is_missing(val):
            return val is None or (isinstance(val, str) and val.strip() == '')

        # Only require fields relevant to selected logistics_type
        if logistics_type == 'BOTH':
            if is_missing(internal_budget):
                self.add_error('internal_budget', 'This field is required for BOTH logistics.')
            if is_missing(external_budget):
                self.add_error('external_budget', 'This field is required for BOTH logistics.')
            if is_missing(sponsor_name):
                self.add_error('sponsor_name', 'This field is required for BOTH logistics.')
        elif logistics_type == 'INTERNAL':
            if is_missing(internal_budget):
                self.add_error('internal_budget', 'This field is required for INTERNAL logistics.')
        elif logistics_type == 'EXTERNAL':
            if is_missing(external_budget):
                self.add_error('external_budget', 'This field is required for EXTERNAL logistics.')
            if is_missing(sponsor_name):
                self.add_error('sponsor_name', 'This field is required for EXTERNAL logistics.')
        return cleaned_data
