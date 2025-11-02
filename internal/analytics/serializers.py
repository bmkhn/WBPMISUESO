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

# --- Helper Serializers (for nested data) ---

class UserSimpleSerializer(serializers.ModelSerializer):
    """ Simple read-only serializer for user info. """
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')
        read_only = True

class AgendaSimpleSerializer(serializers.ModelSerializer):
    """ Simple read-only serializer for the linked Agenda. """
    class Meta:
        model = Agenda
        fields = ('id', 'name')  # <-- Changed 'title' to 'name' and removed other fields
        read_only = True

class SustainableDevelopmentGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = SustainableDevelopmentGoal
        fields = ('goal_number', 'name')
        read_only = True

class ProjectDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDocument
        fields = ('id', 'file', 'document_type', 'uploaded_at', 'description', 'name', 'size', 'extension')
        read_only = True

class ProjectEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectEvent
        fields = ('id', 'title', 'description', 'datetime', 'location', 'status', 'get_image_url')
        read_only = True

class ProjectEvaluationSerializer(serializers.ModelSerializer):
    evaluated_by = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = ProjectEvaluation
        fields = ('id', 'evaluated_by', 'created_at', 'comment', 'rating')
        read_only = True


# --- Main Project Serializer (Read-Only) ---

class ProjectReadOnlySerializer(serializers.ModelSerializer):
    """
    This serializer brings "everything related" together for READ-ONLY display.
    """
    
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
        # This will automatically include all direct fields and the
        # nested related fields defined above.
        fields = '__all__'
        read_only = True