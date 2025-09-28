from django import forms
from .models import Project, ProjectDocument, SustainableDevelopmentGoal
from django.contrib.auth import get_user_model

User = get_user_model()

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'title', 'project_leader', 'agenda', 'project_type',
            'estimated_events', 'estimated_trainees', 'primary_beneficiary', 'primary_location',
            'logistics_type', 'internal_budget', 'external_budget', 'sponsor_name',
            'start_date', 'estimated_end_date'
        ]
