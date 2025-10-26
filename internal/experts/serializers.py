# pasttimer/visual/Visual-5650bbfce2f4db863a5e0a8090389bdc077dc967/internal/experts/serializers.py

from rest_framework import serializers
# Assuming User and College models are defined here
from system.users.models import College, User 

class CollegeSerializer(serializers.ModelSerializer):
    class Meta:
        model = College
        fields = ('id', 'name', 'acronym') # Include relevant fields

class ExpertUserSerializer(serializers.ModelSerializer):
    """Serializer for the Expert User Model (Subset of User fields)."""
    college = CollegeSerializer(read_only=True)
    profile_picture = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'full_name', 'email', 'campus', 'college', 
            'is_expert', 'is_confirmed', 'profile_picture'
        )
        
    def get_profile_picture(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url
        return None
        
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"