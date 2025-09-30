from django import forms
from .models import Project, ProjectEvent


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'title', 'project_leader', 'agenda', 'project_type',
            'estimated_events', 'estimated_trainees', 'primary_beneficiary', 'primary_location',
            'logistics_type', 'internal_budget', 'external_budget', 'sponsor_name',
            'start_date', 'estimated_end_date'
        ]

class ProjectEventForm(forms.ModelForm):
    class Meta:
        model = ProjectEvent
        fields = ['title', 'description', 'datetime', 'location', 'image']