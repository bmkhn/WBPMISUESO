# internal/experts/serializers.py

from rest_framework import serializers
from system.users.models import User, College


class CollegeSerializer(serializers.ModelSerializer):
    """Serializer for the College model."""
    class Meta:
        model = College
        fields = ['id', 'name']


class ExpertSerializer(serializers.ModelSerializer):
    """Full serializer for the User model, focused on expert details."""
    full_name = serializers.SerializerMethodField()
    college = CollegeSerializer(read_only=True) 
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    campus_display = serializers.CharField(source='get_campus_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'role_display', 'college', 'expertise', 
            'is_expert', 'campus_display', 'email', 'contact_no', 'created_at'
        ]

    def get_full_name(self, obj):
        """Uses the get_full_name method on the User model."""
        return obj.get_full_name()