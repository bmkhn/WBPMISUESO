from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Project, ProjectExpense
from .serializers import ProjectExpenseSerializer
from system.api.authentication import APIKeyUserAuthentication
from system.api.permissions import TieredAPIPermission


class ProjectExpenseViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for managing ProjectExpense instances, scoped by the parent Project.
    Only project leaders, providers, or staff/superusers can manage expenses.
    """
    serializer_class = ProjectExpenseSerializer
    authentication_classes = [APIKeyUserAuthentication] 
    permission_classes = [TieredAPIPermission]
    
    def get_project(self):
        """Helper to retrieve and validate the project from URL kwargs."""
        project_pk = self.kwargs.get('project_pk')
        return get_object_or_404(Project, pk=project_pk)

    def check_permissions_and_membership(self, project):
        """Checks if the user is a superuser, staff, project leader, or provider."""
        user = self.request.user
        if (
            user.is_superuser or 
            user.is_staff or 
            user == project.project_leader or 
            project.providers.filter(pk=user.pk).exists()
        ):
            return True
        raise PermissionDenied("You do not have permission to manage expenses for this project.")

    def get_queryset(self):
        # 1. Scope the queryset to the project in the URL
        project = self.get_project()
        
        # 2. Check if the user is authorized to view expenses
        self.check_permissions_and_membership(project)

        # 3. Return the scoped and ordered queryset
        return ProjectExpense.objects.filter(project=project).order_by('-date_incurred')

    def perform_create(self, serializer):
        # Automatically set 'project' based on URL and 'created_by' to the current user
        project = self.get_project()
        
        # Re-check permissions before creation
        self.check_permissions_and_membership(project)

        serializer.save(project=project, created_by=self.request.user)

    def perform_update(self, serializer):
        # Use get_object for detail actions (PUT/PATCH)
        self.check_permissions_and_membership(self.get_object().project)
        serializer.save()

    def perform_destroy(self, instance):
        # Check permissions on the project the expense belongs to
        self.check_permissions_and_membership(instance.project)
        instance.delete()