from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication 
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from decimal import Decimal

from .models import Project, ProjectExpense
from .serializers import ProjectExpenseSerializer
from shared.budget.models import BudgetHistory 
from system.api.permissions import TieredAPIPermission


class ProjectExpenseViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for managing ProjectExpense instances, scoped by the parent Project.
    Only project leaders, providers, or staff/superusers can manage expenses.
    """
    serializer_class = ProjectExpenseSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication] 
    permission_classes = [IsAuthenticated, TieredAPIPermission]
    
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

    def _update_project_used_budget(self, project):
        """Recalculate and save the total used budget for the project."""
        spent = ProjectExpense.objects.filter(project=project).aggregate(s=Sum('amount'))['s'] or Decimal('0')
        project.used_budget = spent
        project.save(update_fields=['used_budget'])

    def _validate_budget_availability(self, project, new_amount, instance=None):
        """
        Check if adding/updating this expense exceeds the total budget.
        """
        total_budget = (project.internal_budget or Decimal('0')) + (project.external_budget or Decimal('0'))
        
        # Calculate current spent excluding the instance being updated (if any)
        expenses = ProjectExpense.objects.filter(project=project)
        if instance:
            expenses = expenses.exclude(pk=instance.pk)
            
        current_spent = expenses.aggregate(s=Sum('amount'))['s'] or Decimal('0')
        
        if (current_spent + new_amount) > total_budget:
            remaining = max(Decimal('0'), total_budget - current_spent)
            raise ValidationError(
                f"Expense amount ({new_amount}) exceeds remaining project budget ({remaining})."
            )

    def perform_create(self, serializer):
        project = self.get_project()
        self.check_permissions_and_membership(project)

        amount = serializer.validated_data.get('amount', Decimal('0'))
        title = serializer.validated_data.get('title', 'Expense')

        # 1. Validate Budget
        self._validate_budget_availability(project, amount)

        # 2. Save Expense
        instance = serializer.save(project=project, created_by=self.request.user)

        # 3. Update Project Totals
        self._update_project_used_budget(project)

        # 4. Log to Budget History (Consistency with views.py)
        try:
            BudgetHistory.objects.create(
                action='SPENT',
                amount=amount,
                description=f'Expense recorded via API for {project.title}: ₱{amount:,.2f} - {title}',
                user=self.request.user
            )
        except Exception:
            # Fail silently if logging fails, similar to view logic
            pass

    def perform_update(self, serializer):
        instance = self.get_object()
        project = instance.project
        self.check_permissions_and_membership(project)

        new_amount = serializer.validated_data.get('amount', instance.amount)
        
        # 1. Validate Budget (treating it as a modification)
        self._validate_budget_availability(project, new_amount, instance)

        # 2. Save
        serializer.save()

        # 3. Update Project Totals
        self._update_project_used_budget(project)

    def perform_destroy(self, instance):
        project = instance.project
        self.check_permissions_and_membership(project)
        
        instance.delete()
        
        # Update Project Totals after deletion
        self._update_project_used_budget(project)