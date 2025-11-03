from rest_framework import serializers
from .models import ClientRequest

class ClientRequestSerializer(serializers.ModelSerializer):
    """
    Serializes all fields on the ClientRequest model.
    The user-related fields and timestamps are set to read-only 
    as they are typically managed by the system or view logic.
    """

    class Meta:
        model = ClientRequest
        fields = '__all__'
        read_only_fields = (
            'submitted_by',
            'submitted_at',
            'reviewed_by',
            'review_at',
            'reason',
            'endorsed_by',
            'endorsed_at',
            'updated_at',
            'updated_by',
        )