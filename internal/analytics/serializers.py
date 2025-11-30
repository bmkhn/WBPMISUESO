from rest_framework import serializers
from shared.projects.models import (
    Project, 
    SustainableDevelopmentGoal, 
    ProjectDocument, 
    ProjectEvent, 
    ProjectEvaluation
)
from internal.agenda.models import Agenda
from system.users.models import User
from typing import Optional, List

#Helper Serializers
class ProjectPublicSerializer(serializers.Serializer):
    """ Defines the fields returned by get_public_projects. """
    title = serializers.CharField(max_length=255)
    status = serializers.CharField(max_length=1000)
    start_date = serializers.DateField()
    end_date = serializers.DateField()

class UserSimpleSerializer(serializers.ModelSerializer):
    """ Simple read-only serializer for user info. """
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        read_only_fields = fields 

class AgendaSimpleSerializer(serializers.ModelSerializer):
    """ Simple read-only serializer for the linked Agenda. """
    class Meta:
        model = Agenda
        fields = ('name',) 
        read_only_fields = fields

class SustainableDevelopmentGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = SustainableDevelopmentGoal
        fields = ('name',)
        read_only_fields = fields

class ProjectDocumentSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    extension = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectDocument
        fields = ('file', 'document_type', 'uploaded_at', 'description', 'name', 'size', 'extension')
        read_only_fields = fields

    def get_name(self, obj) -> str:
        return obj.file.name.split('/')[-1]

    def get_size(self, obj) -> int:
        return obj.file.size
    
    def get_extension(self, obj) -> str:
        return obj.file.name.split('.')[-1]


class ProjectEventSerializer(serializers.ModelSerializer):
    get_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectEvent
        fields = ('title', 'description', 'datetime', 'location', 'status', 'get_image_url')
        read_only_fields = fields
        
    def get_get_image_url(self, obj) -> str:
        return obj.image.url if obj.image else ""


class ProjectEvaluationSerializer(serializers.ModelSerializer):
    evaluated_by = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = ProjectEvaluation
        fields = ('evaluated_by', 'created_at', 'comment', 'rating')
        read_only_fields = fields


class ProjectReadOnlySerializer(serializers.ModelSerializer):
    """
    This serializer id for READ-ONLY display. Additional for spectacular yml added
    """
    duration = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    further_action = serializers.SerializerMethodField()
    
    # --- Nested Serializers for Related Data ---
    documents = ProjectDocumentSerializer(many=True, read_only=True)
    events = ProjectEventSerializer(many=True, read_only=True)
    evaluations = ProjectEvaluationSerializer(many=True, read_only=True)
    
    # --- Simple Serializers for FK/M2M relationships ---
    project_leader = UserSimpleSerializer(read_only=True)
    providers = UserSimpleSerializer(many=True, read_only=True)
    agenda = AgendaSimpleSerializer(read_only=True)
    sdgs = SustainableDevelopmentGoalSerializer(many=True, read_only=True)
    
    class Meta:
        model = Project
        fields = '__all__'
        read_only = True
    
    def get_duration(self, obj) -> str: 
        """Calculates duration in years/days."""
        if obj.start_date and obj.estimated_end_date:
            duration = obj.estimated_end_date - obj.start_date
            years = duration.days // 365
            days = duration.days % 365
            return f"{years} years, {days} days"
        return "N/A"

    def get_status(self, obj) -> str: 
        return obj.get_status_display() 

    def get_further_action(self, obj) -> Optional[List[str]]:
        """Get further action from final submission type if project is completed."""
        if obj.status != 'COMPLETED':
            return None
        
        # Get final submissions for this project
        # Using local import to avoid circular dependency
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

#YML new serializer class for Missing Error
class ProjectAggregationSerializer(serializers.Serializer):
    """ Defines the expected aggregated output for the API view. """
    total_projects = serializers.IntegerField(help_text="The total number of projects.")
    completed_projects = serializers.IntegerField(help_text="The count of projects with a 'Completed' status.")
    projects_by_status = serializers.JSONField(help_text="A dictionary detailing projects counts by status.")