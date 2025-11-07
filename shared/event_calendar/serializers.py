from rest_framework import serializers
from .models import MeetingEvent
from system.users.models import User  # Assuming this is your user model path

class MeetingEventSerializer(serializers.ModelSerializer):
    """
    Serializes all fields on the MeetingEvent model.
    
    'created_by' and 'updated_by' are set to read-only because
    they will be automatically populated by the request user.
    """
    
    # Use PrimaryKeyRelatedField if you want to pass just the user IDs for participants
    participants = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        many=True, 
        allow_empty=True
    )
    
    # Include the attachment file field
    notes_attachment = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = MeetingEvent
        fields = '__all__'  # This includes all fields from your model
        read_only_fields = ('created_by', 'updated_by')