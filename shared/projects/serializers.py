from rest_framework import serializers
from .models import ProjectExpense

class ProjectExpenseSerializer(serializers.ModelSerializer):
    # Read-only fields to show who created the expense
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    
    class Meta:
        model = ProjectExpense
        fields = [
            'project', 
            'title', 
            'reason', 
            'amount', 
            'date_incurred', 
            'receipt',
            'created_by', 
            'created_by_username', 
            'created_at',
        ]
        # created_by and created_at will be set automatically by the system/view
        read_only_fields = ['created_by', 'created_by_username', 'created_at']