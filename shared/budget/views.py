# in shared/budget/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.contrib import messages
from django.core.paginator import Paginator
from decimal import Decimal

# Import your standard role decorator
from system.users.decorators import role_required
from system.users.models import College
from shared.projects.models import Project

from .models import CollegeBudget, BudgetPool, ExternalFunding, BudgetHistory
from .forms import AnnualBudgetForm, CollegeAllocationForm, ProjectInternalBudgetForm, ExternalFundingEditForm
from .services import BudgetService, get_current_fiscal_year

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
    The service layer determines which data (Admin, College, Faculty) to show.
    """
    service = BudgetService()
    context = service.get_role_based_data(request.user)
    context["base_template"] = get_templates(request)
    context["title"] = f"Budget Dashboard ({context['current_year']})"

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
    Admins (VP, etc.) see the College Allocation manager.
    College Admins (Dean, etc.) see the Project Internal Budget assignment form.
    """
    service = BudgetService()
    context = service.get_edit_page_data(request.user)
    context["base_template"] = get_templates(request)
    context["title"] = "Edit Budget"
    
    user_role = getattr(request.user, 'role', None)
    context["user_role"] = user_role # Pass user_role to template
    
    # --- Form Handling for College Admins (Project Assignment) ---
    if user_role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        # Get projects for the form dropdown
        user_college = getattr(request.user, 'college', None)
        projects_for_form = Project.objects.filter(
            project_leader__college=user_college,
            start_date__year=service.fiscal_year
        ).order_by('title')

        if request.method == "POST" and 'assign_project_budget' in request.POST:
            project_form = ProjectInternalBudgetForm(request.POST)
            project_form.fields['project'].queryset = projects_for_form
            
            if project_form.is_valid():
                project = project_form.cleaned_data['project']
                new_budget = project_form.cleaned_data['internal_budget']
                try:
                    service.update_project_internal_budget(request.user, project.id, new_budget)
                    messages.success(request, f'Internal budget for {project.title} updated to ₱{new_budget:,.2f}.')
                    return redirect('budget_edit')
                except (ValueError, PermissionError) as e:
                    messages.error(request, f'Allocation Failed: {e}')
            else:
                messages.error(request, 'Form validation failed.')
        else:
            # GET request
            project_form = ProjectInternalBudgetForm()
            project_form.fields['project'].queryset = projects_for_form
        
        context['project_form'] = project_form

    # --- Form Handling for Admins (College Cut Allocation) ---
    if user_role in ["VP", "DIRECTOR", "UESO"]:
        if request.method == "POST" and 'assign_college_budget' in request.POST:
            
            # --- START: ALL BUG FIXES & VALIDATIONS ---
            try:
                total_proposed_allocation = Decimal('0.00')
                allocations_to_process = []

                # 1. Check if Annual Pool is set
                annual_pool = service.current_pool
                if not annual_pool:
                    messages.error(request, "Annual Budget Pool is not set. Cannot make allocations.")
                    return redirect('budget_edit')

                # 2. First validation loop: Check for negatives and calculate total
                for key, value in request.POST.items():
                    if key.startswith('college_') and value:
                        try:
                            amount = Decimal(str(value).replace(',', '').strip())
                            
                            # BUG FIX 3: Check for negative values
                            if amount < Decimal('0.00'):
                                raise ValueError(f"Negative value (₱{amount:,.2f}) not allowed.")
                            
                            total_proposed_allocation += amount
                            allocations_to_process.append({'key': key, 'amount': amount})

                        except Exception as e:
                            messages.error(request, f"Invalid value detected for {key}: {e}")
                            return redirect('budget_edit')

                # BUG FIX 1: Check against annual pool
                if total_proposed_allocation > annual_pool.total_available:
                    messages.error(request, f"Total proposed allocation (₱{total_proposed_allocation:,.2f}) exceeds the annual pool (₱{annual_pool.total_available:,.2f}).")
                    return redirect('budget_edit')
                
                # 3. Second loop: Check committed funds and save
                with transaction.atomic():
                    colleges_updated = 0
                    for item in allocations_to_process:
                        key = item['key']
                        amount = item['amount']
                        
                        college_id = key.replace('college_', '') 
                        college = College.objects.get(id=college_id) 
                        
                        allocation, created = CollegeBudget.objects.get_or_create(
                            college=college,
                            fiscal_year=service.fiscal_year,
                            defaults={'total_assigned': amount, 'assigned_by': request.user, 'status': 'ACTIVE'}
                        )
                        
                        # BUG FIX 2: Check if new amount is less than already committed amount
                        committed_amount = allocation.total_committed_to_projects or Decimal('0.00')
                        if amount < committed_amount:
                            # Roll back the entire transaction
                            raise Exception(f"Cannot set {college.name} budget to ₱{amount:,.2f}. It already has ₱{committed_amount:,.2f} committed to projects.") 

                        if not created and (allocation.total_assigned != amount or allocation.status != 'ACTIVE'):
                            previous_assigned = allocation.total_assigned
                            allocation.total_assigned = amount
                            allocation.assigned_by = request.user
                            allocation.status = 'ACTIVE' # Ensure status is active
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
                # --- START: FIX for Bug 3 ---
                # Catch the specific error from the transaction
                messages.error(request, f'An error occurred: {e}')
                return redirect('budget_edit') # <-- THIS IS THE CRITICAL FIX
                # --- END: FIX for Bug 3 ---
            # --- END: ALL BUG FIXES & VALIDATIONS ---

    return render(request, 'budget/edit_budget.html', context)

# ------------------------------ 3. HISTORY PAGE ------------------------------
@role_required(["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"], require_confirmed=True)
def budget_history_view(request):
    """Renders the 'history.html' template with pagination."""
    service = BudgetService()
    history_queryset = service.get_budget_history(request.user, request.GET)
    
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
    service = BudgetService()
    sponsor_queryset = service.get_external_funding_list(request.GET)
    
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
    service = BudgetService(fiscal_year=current_year)

    if service.current_pool:
        messages.info(request, 'Budget already initialized for this year.')
        return redirect('budget_dashboard')

    if request.method == 'POST':
        form = AnnualBudgetForm(request.POST)
        if form.is_valid():
            try:
                # BUG FIX 3: Check for negative values
                annual_total = form.cleaned_data['annual_total']
                if annual_total < Decimal('0.00'):
                    messages.error(request, "Annual budget cannot be negative.")
                else:
                    service.set_annual_budget_pool(request.user, current_year, annual_total)
                    messages.success(request, f'Set annual budget for {current_year} to ₱{annual_total:,.2f}.')
                    return redirect('budget_dashboard')
            except Exception as e:
                messages.error(request, f'Error initializing budget: {e}')
    else:
        form = AnnualBudgetForm(initial={'fiscal_year': current_year})

    return render(request, 'budget/setup_annual_budget.html', {"base_template": get_templates(request), "form": form, "title": "Set Up Annual Budget"})