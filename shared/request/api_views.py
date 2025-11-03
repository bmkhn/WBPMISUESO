from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
# Ensure you have a way to import the serializer defined in the previous step
from .serializers import ClientRequestSerializer
from .models import ClientRequest


class ClientRequestViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing and editing ClientRequest instances.
    Provides standard CRUD operations for client requests.
    """
    serializer_class = ClientRequestSerializer
    permission_classes = [IsAuthenticated] # Ensures only logged-in users can interact

    def get_queryset(self):
        """
        Customizes the queryset: Staff and superusers see all requests,
        other authenticated users only see their own submitted requests.
        """
        user = self.request.user
        if user.is_superuser or user.is_staff: 
            return ClientRequest.objects.all().order_by('-submitted_at')
        
        return ClientRequest.objects.filter(submitted_by=user).order_by('-submitted_at')

    def perform_create(self, serializer):
        """
        Automatically sets the 'submitted_by' field to the current user and 
        sets the initial 'status' to 'RECEIVED'.
        """
        # Set initial status to 'RECEIVED' (based on your model choices)
        serializer.save(submitted_by=self.request.user, status='RECEIVED')