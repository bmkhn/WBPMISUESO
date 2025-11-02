# in shared/budget/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.contrib import messages
from django.core.paginator import Paginator
from decimal import Decimal
import json # <-- Import json for the JS solution
from django.utils import timezone # <-- Import timezone
from django.db.models import Q # <-- Import Q

# Import your standard role decorator
from system.users.decorators import role_required
from system.users.models import College
from shared.projects.models import Project

from .models import CollegeBudget, BudgetPool, ExternalFunding, BudgetHistory
from .forms import AnnualBudgetForm, CollegeAllocationForm, ProjectInternalBudgetForm, ExternalFundingEditForm
# DO NOT import BudgetService

# -----------------------------------------------------------------
# START: All logic from services.py is now here, simplified.
# -----------------------------------------------------------------

def get_current_fiscal_year():
    """Determines the current fiscal year."""
    return str(timezone.now().year)

def _get_admin_dashboard_data(fiscal_year):
    """Retrieves system-wide budget data for the Admin Dashboard."""
    
    all_colleges = College.objects.all().order_by('name')
    budget_map = {
        cb.college_id: cb for cb in CollegeBudget.objects.filter(
            status='ACTIVE',
            fiscal_year=fiscal_year
        )
    }
    
    dashboard_data = [] 
    total_committed_agg = Decimal('0')
    total_assigned_to_colleges = Decimal('0')
    
    for college in all_colleges:
        college_budget = budget_map.get(college.id)
        
        if college_budget:
            committed = college_budget.total_committed_to_projects
            original_cut = college_budget.total_assigned
            uncommitted_remaining = college_budget.uncommitted_remaining
            
            total_committed_agg += committed
            total_assigned_to_colleges += original_cut
        else:
            committed, original_cut, uncommitted_remaining = (Decimal('0'), Decimal('0'), Decimal('0'))

        dashboard_data.append({
            'id': college_budget.id if college_budget else None,
            'college_id': college.id, 
            'college_name': college.name,
            'original_cut': original_cut, # Initial Budget
            'committed_funding': committed, # Internal Budget
            'uncommitted_remaining': uncommitted_remaining, # Remaining
        })
        
    current_pool = BudgetPool.objects.filter(fiscal_year=fiscal_year).first()
    pool_available = current_pool.total_available if current_pool else Decimal('0')
    pool_unallocated_remaining = pool_available - total_assigned_to_colleges
    
    return {
        "is_setup": current_pool is not None,
        "pool_available": pool_available,
        "pool_unallocated_remaining": pool_unallocated_remaining,
        "total_assigned_to_colleges": total_assigned_to_colleges,
        "total_committed_to_projects_agg": total_committed_agg,
        "dashboard_data": dashboard_data,
    }

def _get_college_dashboard_data(user, fiscal_year):
    """Retrieves college-specific data and its funded projects."""
    user_college = getattr(user, 'college', None)
    if not user_college: 
        return {"is_setup": True, "error": "User is not assigned to a College."}
        
    college_budget = CollegeBudget.objects.filter(
        college=user_college,
        fiscal_year=fiscal_year,
        status='ACTIVE'
    ).first()
    
    if not college_budget: 
        return {"is_setup": False, "college_name": user_college.name}

    projects = Project.objects.filter(
        project_leader__college=user_college,
        start_date__year=fiscal_year 
    ).select_related('project_leader').order_by('title')
    
    project_list = []
    for project in projects:
        # --- SIMPLIFIED as requested ---
        assigned = project.internal_budget or Decimal('0')
        external = project.external_budget or Decimal('0')
        
        project_list.append({
            'id': project.id,
            'title': project.title,
            'status': project.get_status_display(),
            'internal_funding_committed': assigned,
            'external_funding_committed': external,
        })
        
    return {
        'is_setup': True,
        'college_budget': college_budget,
        'college_name': user_college.name,
        'total_assigned_original_cut': college_budget.total_assigned, # Initial Budget
        'total_committed_to_projects': college_budget.total_committed_to_projects, # Internal Budget
        'uncommitted_remaining': college_budget.uncommitted_remaining, # Remaining
        'dashboard_data': project_list
    }

def _get_faculty_dashboard_data(user):
    """RetrieVes project data for Faculty/Implementers."""
    user_projects = Project.objects.filter(
        Q(project_leader=user) | Q(providers=user)
    ).distinct().select_related('project_leader__college').order_by('title')
    
    project_data = []
    total_internal = Decimal('0')
    total_external = Decimal('0')
    
    for project in user_projects:
        # --- SIMPLIFIED as requested ---
        assigned = project.internal_budget or Decimal('0')
        external = project.external_budget or Decimal('0')
        
        total_internal += assigned
        total_external += external
        
        project_data.append({
            'id': project.id,
            'title': project.title,
            'status': project.get_status_display(),
            'internal_funding': assigned,
            'external_funding': external,
        })
        
    return {
        "is_setup": True, 
        "dashboard_data": project_data,
        "total_internal": total_internal,
        "total_external": total_external,
        "total_assigned": total_internal + total_external,
    }

def _get_edit_page_data(user, fiscal_year):
    """Gets data for the combined 'edit_budget.html' template."""
    user_role = getattr(user, 'role', None)
    context = {}
    
    if user_role in ["VP", "DIRECTOR", "UESO"]:
        admin_data = _get_admin_dashboard_data(fiscal_year)
        context['colleges_data'] = admin_data['dashboard_data']
        # This map is used by the JavaScript solution
        context['allocation_map'] = json.dumps({
            item['college_id']: item['original_cut'] for item in admin_data['dashboard_data']
        })

    if user_role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        college_data = _get_college_dashboard_data(user, fiscal_year)
        context.update(college_data)
    
    return context

@transaction.atomic
def _set_annual_budget_pool(user, fiscal_year, total_available):
    """Creates or updates the single annual BudgetPool."""
    
    if total_available < Decimal('0.00'):
        raise ValueError("Annual budget pool cannot be negative.")

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
def _update_project_internal_budget(user, project_id, new_internal_budget):
    """Updates a Project's internal budget after validating against CollegeBudget."""
    
    if new_internal_budget < Decimal('0.00'):
        raise ValueError("Internal budget cannot be negative.")

    project = Project.objects.select_related('project_leader__college').get(id=project_id)
    
    if not project.project_leader or not project.project_leader.college:
        raise PermissionError("Project leader or their college is required for internal budget assignment.")

    if project.project_leader.college != getattr(user, 'college', None):
        raise PermissionError("You can only assign budgets to projects from your own college.")

    fiscal_year = get_current_fiscal_year()
    try:
        college_budget = CollegeBudget.objects.get(
            college=project.project_leader.college, 
            fiscal_year=fiscal_year,
        )
    except CollegeBudget.DoesNotExist:
        raise PermissionError(f"No budget found for {project.project_leader.college.name} for {fiscal_year}. Please contact the administrator.")
    
    old_budget = project.internal_budget or Decimal('0')
    commitment_delta = new_internal_budget - old_budget
    
    if college_budget.uncommitted_remaining - commitment_delta < Decimal('0'):
         raise ValueError(f"Assignment exceeds remaining college budget by ₱{abs(college_budget.uncommitted_remaining - commitment_delta):,.2f}.")

    project.internal_budget = new_internal_budget
    project.save(update_fields=['internal_budget'])
    
    college_budget.total_committed_to_projects = (college_budget.total_committed_to_projects or Decimal('0.00')) + commitment_delta
    college_budget.save(update_fields=['total_committed_to_projects'])
    
    BudgetHistory.objects.create(
        college_budget=college_budget,
        action='ADJUSTED' if new_internal_budget < old_budget else 'ALLOCATED',
        amount=commitment_delta,
        description=f'Project "{project.title}" internal budget set to ₱{new_internal_budget:,.2f}. Funded by {college_budget.college.name}.',
        user=user
    )
    return project

# -----------------------------------------------------------------
# END: Logic from services.py
# -----------------------------------------------------------------


# --- HELPER TO GET BASE TEMPLATE ---
def get_templates(request):
    """Determines the base template based on user role."""
    user_role = getattr(request.user, 'role', None)
    # All budget users use the internal template
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR", "FACULTY", "IMPLEMENTER"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html" 
    return base_template

# ------------------------------ 1. BUDGET DASHBOARD ------------------------------
@role_required(["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR", "FACULTY", "IMPLEMENTER"], require_confirmed=True)
def budget_view(request):
    """
    Renders the main 'budget.html' template.
    All logic is now handled by local functions.
    """
    current_year = get_current_fiscal_year()
    user_role = getattr(request.user, 'role', None)
        
    if user_role in ["VP", "DIRECTOR", "UESO"]:
        context = _get_admin_dashboard_data(current_year)
    elif user_role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        context = _get_college_dashboard_data(request.user, current_year)
    elif user_role in ["FACULTY", "IMPLEMENTER"]:
        context = _get_faculty_dashboard_data(request.user)
    else:
        context = {"is_setup": False, "error": "Invalid User Role"}
    
    # Add common context
    context["latest_history"] = BudgetHistory.objects.all().order_by('-timestamp')[:5]
    context["latest_funding"] = ExternalFunding.objects.filter(status__in=['APPROVED', 'PENDING']).order_by('-proposal_date')[:5]
    context["base_template"] = get_templates(request)
    context["title"] = f"Budget Dashboard ({current_year})"
    context["user_role"] = user_role
    context["is_admin"] = user_role in ["VP", "DIRECTOR", "UESO"]
    context["is_college_admin"] = user_role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]

    if not context.get('is_setup', True):
        if context.get('user_role') in ["VP", "DIRECTOR", "UESO"]:
            messages.info(request, "Annual Budget Pool not initialized. Please set it up.")
            return redirect('budget_setup')
        return render(request, 'budget/no_budget_setup.html', context)

    return render(request, 'budget/budget.html', context)

# ------------------------------ 2. EDIT BUDGET PAGE ------------------------------
@role_required(["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"], require_confirmed=True)
def edit_budget_view(request):
    """
    Renders the 'edit_budget.html' template.
    All logic is now handled by local functions.
    """
    current_year = get_current_fiscal_year()
    context = _get_edit_page_data(request.user, current_year)
    context["base_template"] = get_templates(request)
    context["title"] = "Edit Budget"
    
    user_role = getattr(request.user, 'role', None)
    context["user_role"] = user_role 
    
    # --- Form Handling for College Admins (Project Assignment) ---
    if user_role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        user_college = getattr(request.user, 'college', None)
        projects_for_form = Project.objects.filter(
            project_leader__college=user_college,
            start_date__year=current_year
        ).order_by('title')

        if request.method == "POST" and 'assign_project_budget' in request.POST:
            project_form = ProjectInternalBudgetForm(request.POST)
            project_form.fields['project'].queryset = projects_for_form
            
            if project_form.is_valid():
                project = project_form.cleaned_data['project']
                new_budget = project_form.cleaned_data['internal_budget']
                try:
                    _update_project_internal_budget(request.user, project.id, new_budget) # Use local function
                    messages.success(request, f'Internal budget for {project.title} updated to ₱{new_budget:,.2f}.')
                    return redirect('budget_edit')
                except (ValueError, PermissionError) as e:
                    messages.error(request, f'Allocation Failed: {e}')
            else:
                messages.error(request, 'Form validation failed.')
        else:
            project_form = ProjectInternalBudgetForm()
            project_form.fields['project'].queryset = projects_for_form
        
        context['project_form'] = project_form

    # --- Form Handling for Admins (College Cut Allocation) ---
    if user_role in ["VP", "DIRECTOR", "UESO"]:
        if request.method == "POST" and 'assign_college_budget' in request.POST:
            
            try:
                total_proposed_allocation = Decimal('0.00')
                allocations_to_process = []

                current_pool = BudgetPool.objects.filter(fiscal_year=current_year).first()
                if not current_pool:
                    messages.error(request, "Annual Budget Pool is not set. Cannot make allocations.")
                    return redirect('budget_edit')

                for key, value in request.POST.items():
                    if key.startswith('college_') and value:
                        try:
                            amount = Decimal(str(value).replace(',', '').strip())
                            
                            if amount < Decimal('0.00'):
                                raise ValueError(f"Negative value (₱{amount:,.2f}) not allowed.")
                            
                            total_proposed_allocation += amount
                            allocations_to_process.append({'key': key, 'amount': amount})

                        except Exception as e:
                            messages.error(request, f"Invalid value detected for {key}: {e}")
                            return redirect('budget_edit')

                if total_proposed_allocation > current_pool.total_available:
                    messages.error(request, f"Total proposed allocation (₱{total_proposed_allocation:,.2f}) exceeds the annual pool (₱{current_pool.total_available:,.2f}).")
                    return redirect('budget_edit')
                
                with transaction.atomic():
                    colleges_updated = 0
                    for item in allocations_to_process:
                        key = item['key']
                        amount = item['amount']
                        
                        college_id = key.replace('college_', '') 
                        college = College.objects.get(id=college_id) 
                        
                        allocation, created = CollegeBudget.objects.get_or_create(
                            college=college,
                            fiscal_year=current_year,
                            defaults={'total_assigned': amount, 'assigned_by': request.user, 'status': 'ACTIVE'}
                        )
                        
                        committed_amount = allocation.total_committed_to_projects or Decimal('0.00')
                        if amount < committed_amount:
                            raise Exception(f"Cannot set {college.name} budget to ₱{amount:,.2f}. It already has ₱{committed_amount:,.2f} committed to projects.") 

                        if not created and (allocation.total_assigned != amount or allocation.status != 'ACTIVE'):
                            previous_assigned = allocation.total_assigned
                            allocation.total_assigned = amount
                            allocation.assigned_by = request.user
                            allocation.status = 'ACTIVE' 
                            allocation.save()
                            
                            BudgetHistory.objects.create(
                                college_budget=allocation,
                                action='ADJUSTED',
                                amount=amount,
                                description=f'College cut adjusted for {college.name}: ₱{previous_assigned:,.2f} → ₱{amount:,.2f}',
                                user=request.user
                            )
                        colleges_updated += 1
                        
                    messages.success(request, f'Successfully updated allocations for {colleges_updated} colleges.')
                    return redirect('budget_edit')
            
            except Exception as e:
                messages.error(request, f'An error occurred: {e}')
                return redirect('budget_edit') # This redirect fixes the "stale data" bug

    return render(request, 'budget/edit_budget.html', context)

# ------------------------------ 3. HISTORY PAGE ------------------------------
@role_required(["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"], require_confirmed=True)
def budget_history_view(request):
    """Renders the 'history.html' template with pagination."""
    
    history_queryset = BudgetHistory.objects.select_related(
            'user', 'college_budget__college', 'external_funding__project'
        ).order_by('-timestamp')
        
    if getattr(request.user, 'role', None) in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        if user_college := getattr(request.user, 'college', None):
            history_queryset = history_queryset.filter(college_budget__college=user_college)
    
    paginator = Paginator(history_queryset, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        "page_obj": page_obj,
        "title": "Budget History Audit Log",
        "base_template": get_templates(request)
    }
    return render(request, 'budget/history.html', context)

# ------------------------------ 4. EXTERNAL SPONSORS PAGE ------------------------------
@role_required(["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR", "FACULTY", "IMPLEMENTER"], require_confirmed=True)
def external_sponsors_view(request):
    """Renders the 'external_sponsors.html' template with pagination."""
    sponsor_queryset = ExternalFunding.objects.select_related('project').filter(
            status__in=['APPROVED', 'COMPLETED', 'PENDING']
        ).order_by('-proposal_date')
    
    paginator = Paginator(sponsor_queryset, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        "page_obj": page_obj,
        "title": "External Sponsors and Funding",
        "base_template": get_templates(request)
    }
    return render(request, 'budget/external_sponsors.html', context)

# ------------------------------ 5. SETUP (Admin Only) ------------------------------
@role_required(["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def setup_annual_budget(request):
    """View for Admins to create the annual BudgetPool."""
    current_year = get_current_fiscal_year()
    current_pool = BudgetPool.objects.filter(fiscal_year=current_year).first()

    if current_pool:
        messages.info(request, 'Budget already initialized for this year.')
        return redirect('budget_dashboard')

    if request.method == 'POST':
        form = AnnualBudgetForm(request.POST)
        if form.is_valid():
            try:
                annual_total = form.cleaned_data['annual_total']
                if annual_total < Decimal('0.00'):
                    messages.error(request, "Annual budget cannot be negative.")
                else:
                    _set_annual_budget_pool(request.user, current_year, annual_total) # Use local function
                    messages.success(request, f'Set annual budget for {current_year} to ₱{annual_total:,.2f}.')
                    return redirect('budget_dashboard')
            except Exception as e:
                messages.error(request, f'Error initializing budget: {e}')
    else:
        form = AnnualBudgetForm(initial={'fiscal_year': current_year})

    return render(request, 'budget/setup_annual_budget.html', {"base_template": get_templates(request), "form": form, "title": "Set Up Annual Budget"})