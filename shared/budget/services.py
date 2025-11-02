# in shared/budget/services.py (New File)

from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
from .models import CollegeBudget, BudgetPool, BudgetHistory, ExternalFunding
from shared.projects.models import Project
from system.users.models import College
from django.db import transaction

def get_current_fiscal_year():
    """Determines the current fiscal year."""
    return str(timezone.now().year)

class BudgetService:
    """Service layer for all complex budget calculations and business logic."""
    
    def __init__(self, fiscal_year=None):
        self.fiscal_year = fiscal_year or get_current_fiscal_year()
        self.current_pool = BudgetPool.objects.filter(fiscal_year=self.fiscal_year).first()

    def get_role_based_data(self, user):
        """Dispatches to the correct data-gathering function based on user role."""
        user_role = getattr(user, 'role', None)
        
        if user_role in ["VP", "DIRECTOR", "UESO"]:
            data = self._get_admin_dashboard_data()
        elif user_role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
            data = self._get_college_dashboard_data(user)
        elif user_role in ["FACULTY", "IMPLEMENTER"]:
            data = self._get_faculty_dashboard_data(user)
        else:
            data = {"is_setup": False, "error": "Invalid User Role"}
        
        # Inject common context
        data["user_role"] = user_role
        data["current_year"] = self.fiscal_year
        data["is_admin"] = user_role in ["VP", "DIRECTOR", "UESO"]
        data["is_college_admin"] = user_role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]

        return data

    def _get_admin_dashboard_data(self):
        """Retrieves system-wide budget data for the Admin Dashboard."""
        
        college_budgets_qs = CollegeBudget.objects.filter(
            status='ACTIVE',
            fiscal_year=self.fiscal_year
        ).select_related('college').order_by('college__name')
        
        total_assigned_to_colleges = college_budgets_qs.aggregate(Sum('total_assigned'))['total_assigned__sum'] or Decimal('0')
        
        dashboard_data = [] # Data for the main table
        total_spent_agg = Decimal('0')
        total_committed_agg = Decimal('0')
        
        for cb in college_budgets_qs:
            spent = cb.total_spent_by_projects 
            committed = cb.total_committed_to_projects 

            total_spent_agg += spent
            total_committed_agg += committed
            
            dashboard_data.append({
                'id': cb.id,
                'college_name': cb.college.name,
                'original_cut': cb.total_assigned,
                'committed_funding': committed, # Project Internal Funding
                'total_spent': spent,
                'final_remaining': cb.final_remaining, # Cut minus Spent
                'uncommitted_remaining': cb.uncommitted_remaining, # Available for new projects
            })
            
        pool_available = self.current_pool.total_available if self.current_pool else Decimal('0')
        pool_unallocated_remaining = pool_available - total_assigned_to_colleges
        
        return {
            "is_setup": self.current_pool is not None,
            "pool_available": pool_available,
            "pool_unallocated_remaining": pool_unallocated_remaining,
            "total_assigned_to_colleges": total_assigned_to_colleges,
            "total_committed_to_projects_agg": total_committed_agg,
            "total_spent_by_projects_agg": total_spent_agg,
            "dashboard_data": dashboard_data,
        }

    def _get_college_dashboard_data(self, user):
        """Retrieves college-specific data and its funded projects."""
        user_college = getattr(user, 'college', None)
        if not user_college: 
            return {"is_setup": True, "error": "User is not assigned to a College."}
            
        college_budget = CollegeBudget.objects.filter(
            college=user_college,
            fiscal_year=self.fiscal_year,
            status='ACTIVE'
        ).first()
        
        if not college_budget: 
            return {"is_setup": False, "college_name": user_college.name}

        projects = Project.objects.filter(
            project_leader__college=user_college,
            start_date__year=self.fiscal_year 
        ).select_related('project_leader').order_by('title')
        
        project_list = []
        for project in projects:
            assigned = project.internal_budget or Decimal('0')
            spent = project.used_budget or Decimal('0')
            project_list.append({
                'id': project.id,
                'title': project.title,
                'status': project.get_status_display(),
                'internal_funding_committed': assigned,
                'total_spent': spent,
                'total_remaining': assigned - spent,
            })
            
        return {
            'is_setup': True,
            'college_budget': college_budget,
            'college_name': user_college.name,
            'total_assigned_original_cut': college_budget.total_assigned,
            'total_spent': college_budget.total_spent_by_projects,
            'total_committed_to_projects': college_budget.total_committed_to_projects,
            'final_remaining': college_budget.final_remaining,
            'uncommitted_remaining': college_budget.uncommitted_remaining,
            'dashboard_data': project_list
        }
    
    def _get_faculty_dashboard_data(self, user):
        """RetrieVes project data for Faculty/Implementers."""
        user_projects = Project.objects.filter(
            Q(project_leader=user) | Q(providers=user)
        ).distinct().select_related('project_leader__college').order_by('title')
        
        project_data = []
        total_assigned = Decimal('0')
        total_spent = Decimal('0')
        
        for project in user_projects:
            assigned = project.internal_budget or Decimal('0')
            spent = project.used_budget or Decimal('0')
            total_assigned += assigned
            total_spent += spent
            
            project_data.append({
                'id': project.id,
                'title': project.title,
                'status': project.get_status_display(),
                'internal_funding': assigned,
                'total_spent': spent,
                'remaining': assigned - spent,
            })
            
        return {
            "is_setup": True, 
            "dashboard_data": project_data,
            "total_assigned": total_assigned,
            "total_spent": total_spent,
            "total_remaining": total_assigned - total_spent,
            "utilization_percentage": round((total_spent / total_assigned * 100) if total_assigned > 0 else 0, 2),
        }

    # --- DATA FOR OTHER PAGES ---
    
    def get_edit_page_data(self, user):
        """Gets data for the combined 'edit_budget.html' template."""
        user_role = getattr(user, 'role', None)
        context = {}
        
        # Admins get data to manage college cuts
        if user_role in ["VP", "DIRECTOR", "UESO"]:
            admin_data = self._get_admin_dashboard_data()
            context['colleges_data'] = admin_data['dashboard_data']
            context['all_colleges'] = College.objects.all().order_by('name')

        # College Admins get data to manage project internal budgets
        if user_role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
            college_data = self._get_college_dashboard_data(user)
            context.update(college_data)
        
        return context

    def get_budget_history(self, user, filters):
        """RetrieVes filtered and paginated budget history."""
        history_qs = BudgetHistory.objects.select_related(
            'user', 'college_budget__college', 'external_funding__project'
        ).order_by('-timestamp')
        
        # Apply role-based filtering
        if getattr(user, 'role', None) in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
            if user_college := getattr(user, 'college', None):
                history_qs = history_qs.filter(college_budget__college=user_college)
        
        # Apply search filters...
        return history_qs

    def get_external_funding_list(self, filters):
        """Retrieves filtered and paginated external funding list."""
        return ExternalFunding.objects.select_related('project').filter(
            status__in=['APPROVED', 'COMPLETED', 'PENDING']
        ).order_by('-proposal_date')

    # --- TRANSACTIONAL METHODS ---

    @transaction.atomic
    def set_annual_budget_pool(self, user, fiscal_year, total_available):
        """Creates or updates the single annual BudgetPool."""
        pool, created = BudgetPool.objects.update_or_create(
            fiscal_year=fiscal_year,
            defaults={'total_available': total_available}
        )
        BudgetHistory.objects.create(
            action='ALLOCATED' if created else 'ADJUSTED',
            amount=pool.total_available,
            description=f'Annual Budget Pool initialized/set for {fiscal_year}: ₱{total_available:,.2f}',
            user=user
        )
        return pool
    
    @transaction.atomic
    def update_project_internal_budget(self, user, project_id, new_internal_budget):
        """Updates a Project's internal budget after validating against CollegeBudget."""
        project = Project.objects.select_related('project_leader__college').get(id=project_id)
        
        if not project.project_leader or not project.project_leader.college:
            raise PermissionError("Project leader or their college is required for internal budget assignment.")

        if project.project_leader.college != getattr(user, 'college', None):
            raise PermissionError("You can only assign budgets to projects from your own college.")

        fiscal_year = get_current_fiscal_year()
        try:
            college_budget = CollegeBudget.objects.get(
                college=project.project_leader.college, 
                fiscal_year=fiscal_year
            )
        except CollegeBudget.DoesNotExist:
            raise PermissionError(f"No active budget found for {project.project_leader.college.name} for {fiscal_year}. Please contact the administrator.")
        
        old_budget = project.internal_budget or Decimal('0')
        commitment_delta = new_internal_budget - old_budget
        
        # Validation
        if college_budget.uncommitted_remaining - commitment_delta < Decimal('0'):
             raise ValueError(f"Assignment exceeds remaining college budget by ₱{abs(college_budget.uncommitted_remaining - commitment_delta):,.2f}.")

        project.internal_budget = new_internal_budget
        project.save()
        
        BudgetHistory.objects.create(
            college_budget=college_budget,
            action='ADJUSTED' if new_internal_budget < old_budget else 'ALLOCATED',
            amount=commitment_delta,
            description=f'Project "{project.title}" internal budget set to ₱{new_internal_budget:,.2f}. Funded by {college_budget.college.name}.',
            user=user
        )
        return project