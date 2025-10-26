# shared/archive/serializers.py (MODIFIED)

from rest_framework import serializers
from shared.projects.models import Project
from system.users.models import User, College # <-- Corrected User and added College
from internal.agenda.models import Agenda 


class CollegeSerializer(serializers.ModelSerializer):
    """Serializer for the College model."""
    class Meta:
        model = College
        fields = ['id', 'name']


class ProjectLeaderSerializer(serializers.ModelSerializer):
    """Serializer for the Project Leader to display full name/username."""
    full_name = serializers.SerializerMethodField()
    college = CollegeSerializer(read_only=True) # <-- Nested College data

    class Meta:
        model = User 
        fields = ['id', 'full_name', 'college']

    def get_full_name(self, obj):
        """Tries to get full name, falls back to username."""
        if hasattr(obj, 'get_full_name') and obj.get_full_name():
            return obj.get_full_name()
        return obj.username 


class AgendaSerializer(serializers.ModelSerializer):
    """Serializer for the Agenda model."""
    class Meta:
        model = Agenda
        fields = ['id', 'name']


class ProjectSerializer(serializers.ModelSerializer):
    """Full serializer for the Project model used in the final list/table view."""
    project_leader = ProjectLeaderSerializer(read_only=True)
    agenda = AgendaSerializer(read_only=True)
    
    progress_display = serializers.CharField(read_only=True) 
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'project_leader', 'agenda', 'start_date', 
            'estimated_end_date', 'progress_display', 'duration',
            'estimated_trainees', 'status'
        ]

    def get_duration(self, obj):
        """Calculates duration in years/days."""
        if obj.start_date and obj.estimated_end_date:
            duration = obj.estimated_end_date - obj.start_date
            years = duration.days // 365
            days = duration.days % 365
            return f"{years} years, {days} days"
        return "N/A"