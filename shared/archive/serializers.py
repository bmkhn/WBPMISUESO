from rest_framework import serializers
from shared.projects.models import Project
from system.users.models import User, College
from internal.agenda.models import Agenda 


class CollegeSerializer(serializers.ModelSerializer):
    """Serializer for the College model."""
    class Meta:
        model = College
        fields = ['id', 'name']


class ProjectLeaderSerializer(serializers.ModelSerializer):
    """Serializer for the Project Leader to display full name/username."""
    full_name = serializers.SerializerMethodField()
    college = CollegeSerializer(read_only=True) 

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
    status = serializers.SerializerMethodField()
    further_action = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'project_leader', 'agenda', 'start_date', 
            'estimated_end_date', 'progress_display', 'duration',
            'estimated_trainees', 'status', 'further_action'
        ]

    def get_status(self, obj):
        return obj.get_status_display()

    def get_duration(self, obj):
        """Calculates duration in years/days."""
        if obj.start_date and obj.estimated_end_date:
            duration = obj.estimated_end_date - obj.start_date
            years = duration.days // 365
            days = duration.days % 365
            return f"{years} years, {days} days"
        return "N/A"
    
    def get_further_action(self, obj):
        """Get further action from final submission type if project is completed."""
        if obj.status != 'COMPLETED':
            return None
        
        # Get final submissions for this project
        from internal.submissions.models import Submission
        final_submissions = Submission.objects.filter(
            project=obj,
            downloadable__submission_type='final'
        ).first()
        
        if not final_submissions:
            return None
        
        actions = []
        if final_submissions.for_product_production:
            actions.append('For Product Production')
        if final_submissions.for_research:
            actions.append('For Research')
        if final_submissions.for_extension:
            actions.append('For Extension')
        
        return actions if actions else None