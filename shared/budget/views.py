from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.contrib import messages
from django.core.paginator import Paginator
from decimal import Decimal
import json
from django.utils import timezone

from django.db.models import Q, Sum, Value, DecimalField, F
from django.db.models.functions import Coalesce, TruncMonth

from system.users.decorators import role_required
from system.users.models import College
from shared.projects.models import Project, ProjectExpense

from .models import CollegeBudget, BudgetPool, ExternalFunding, BudgetHistory

from .forms import AnnualBudgetForm, CollegeAllocationForm, ProjectInternalBudgetForm, ExternalFundingEditForm

from django.http import HttpResponse
import csv


def get_current_fiscal_year():
    return str(timezone.now().year)

def _get_admin_dashboard_data(fiscal_year):
    """
    Build dashboard data for VP/DIRECTOR/UESO roles.
    - Produces actual monthly unallocated pesos (unallocated_data_json)
    - Produces formatted tooltip strings (unallocated_data_raw_json)
    - Produces normalized cumulative data for sparklines
    """
    all_colleges = College.objects.all().order_by('name')

    college_budget_map = {
        cb.college_id: cb for cb in CollegeBudget.objects.filter(
            status='ACTIVE',
            fiscal_year=fiscal_year
        )
    }

    # Aggregate total committed budget for the entire fiscal year for display and normalization
    project_budgets_by_college = Project.objects.filter(
        project_leader__college__isnull=False,
        start_date__year=int(fiscal_year)
    ).values('project_leader__college').annotate(
        total_internal=Coalesce(Sum('internal_budget'), Value(Decimal('0.0')), output_field=DecimalField()),
        total_external=Coalesce(Sum('external_budget'), Value(Decimal('0.0')), output_field=DecimalField())
    ).order_by('project_leader__college')

    project_budget_map = {
        item['project_leader__college']: {
            'internal': item['total_internal'],
            'external': item['total_external']
        }
        for item in project_budgets_by_college
    }

    dashboard_data = []
    total_committed_agg = Decimal('0')
    total_external_agg = Decimal('0')
    total_assigned_to_colleges = Decimal('0')

    for college in all_colleges:
        college_budget = college_budget_map.get(college.id)
        project_metrics = project_budget_map.get(college.id, {'internal': Decimal('0'), 'external': Decimal('0')})

        current_committed = project_metrics['internal']
        current_external = project_metrics['external']

        if college_budget:
            original_cut = college_budget.total_assigned
            uncommitted_remaining = original_cut - current_committed
        else:
            original_cut = Decimal('0')
            uncommitted_remaining = Decimal('0') - current_committed

        total_committed_agg += current_committed
        total_external_agg += current_external
        total_assigned_to_colleges += original_cut

        dashboard_data.append({
            'id': college_budget.id if college_budget else None,
            'college_id': college.id,
            'college_name': college.name,
            'original_cut': original_cut,
            'committed_funding': current_committed,
            'uncommitted_remaining': uncommitted_remaining,
            'external_funding': current_external
        })

    current_pool = BudgetPool.objects.filter(fiscal_year=fiscal_year).first()
    pool_available = current_pool.total_available if current_pool else Decimal('0')
    pool_unallocated_remaining = pool_available - total_assigned_to_colleges

    year_int = int(fiscal_year)

    # --- Monthly Pool Value Calculation ---
    pool_history_qs = BudgetHistory.objects.filter(
        Q(description__icontains='Annual Budget Pool'),
        timestamp__year=year_int
    ).order_by('timestamp')

    pool_values = {i: pool_available for i in range(1, 13)}
    current_pool_value = pool_available
    for history in pool_history_qs:
        current_pool_value = history.amount
        month = history.timestamp.month
        for m in range(month, 13):
            pool_values[m] = current_pool_value

    # --- Monthly Assigned to Colleges Calculation ---
    assigned_cumulatives_raw = {i: Decimal('0') for i in range(1, 13)}
    assigned_history_qs_all = BudgetHistory.objects.filter(
        Q(description__icontains='college cut') | Q(description__icontains='College cut'),
        timestamp__year=year_int,
        action__in=['ALLOCATED', 'ADJUSTED']
    )

    monthly_changes_by_trunc = assigned_history_qs_all.annotate(
        month=TruncMonth('timestamp')
    ).values('month').annotate(
        net_change=Sum('amount')
    ).order_by('month')
    
    monthly_net_changes = {i: Decimal('0') for i in range(1, 13)}
    for item in monthly_changes_by_trunc:
        month_num = item['month'].month
        monthly_net_changes[month_num] = item['net_change']

    assigned_running_total_monthly = Decimal('0')
    for m in range(1, 13):
        assigned_running_total_monthly += monthly_net_changes[m]
        assigned_cumulatives_raw[m] = assigned_running_total_monthly
    
    # Actual unallocated pesos per month (pool - assigned cumulatives)
    unallocated_data_raw = [float((pool_values[m] - assigned_cumulatives_raw[m])) for m in range(1, 13)]

    # Normalized (0-100) values for mini sparkline charts (based on max pool)
    max_pool_available = max(pool_values.values()) if pool_values else Decimal('0')
    max_norm_value = max_pool_available if max_pool_available > Decimal('0') else Decimal('1')

    # --- Normalized Assigned to Colleges Data (for mini chart) ---
    assigned_cumulative_data = []
    for m in range(1, 13):
        running_total = assigned_cumulatives_raw[m]
        if total_assigned_to_colleges > 0:
            normalized_value = (running_total / total_assigned_to_colleges) * 100
            normalized_value = min(100, max(0, int(normalized_value)))
        else:
            normalized_value = 0
        assigned_cumulative_data.append(int(normalized_value))

    # --- Normalized Internal Committed Data (FIXED: Use project start date for cumulative) ---
    # We use Project start_date to track when commitment happened for fluctuation
    project_internal_monthly = Project.objects.filter(
        start_date__year=year_int,
        internal_budget__gt=0
    ).annotate(
        month=TruncMonth('start_date')
    ).values('month').annotate(
        monthly_commitment=Sum('internal_budget')
    ).order_by('month')

    internal_monthly_commitments = {i: Decimal('0') for i in range(1, 13)}
    for item in project_internal_monthly:
        month = item['month'].month
        internal_monthly_commitments[month] = item['monthly_commitment']

    internal_cumulative_data = []
    running_total = Decimal('0')
    for month in range(1, 13):
        running_total += internal_monthly_commitments[month]
        if total_committed_agg > 0:
            normalized_value = (running_total / total_committed_agg) * 100
            normalized_value = min(100, max(0, int(normalized_value)))
        else:
            normalized_value = 0
        internal_cumulative_data.append(int(normalized_value))


    # --- Normalized External Committed Data (FIXED: Use project start date for cumulative) ---
    project_external_monthly = Project.objects.filter(
        start_date__year=year_int,
        external_budget__gt=0
    ).annotate(
        month=TruncMonth('start_date')
    ).values('month').annotate(
        monthly_commitment=Sum('external_budget')
    ).order_by('month')

    external_monthly_commitments = {i: Decimal('0') for i in range(1, 13)}
    for item in project_external_monthly:
        month = item['month'].month
        external_monthly_commitments[month] = item['monthly_commitment']

    external_cumulative_data = []
    running_total = Decimal('0')
    for month in range(1, 13):
        running_total += external_monthly_commitments[month]
        if total_external_agg > 0:
            normalized_value = (running_total / total_external_agg) * 100
            normalized_value = min(100, max(0, int(normalized_value)))
        else:
            normalized_value = 0
        external_cumulative_data.append(int(normalized_value))
    
    # --- JSON Serialization ---
    unallocated_data_json = json.dumps(unallocated_data_raw)
    unallocated_data_raw_json = json.dumps([f"₱{v:,.2f}" for v in unallocated_data_raw])
    assigned_data_json = json.dumps(assigned_cumulative_data)
    internal_committed_data_json = json.dumps(internal_cumulative_data)
    external_data_json = json.dumps(external_cumulative_data)

    return {
        "is_setup": current_pool is not None,
        "pool_available": pool_available,
        "pool_unallocated_remaining": pool_unallocated_remaining,
        "total_assigned_to_colleges": total_assigned_to_colleges,
        "total_committed_to_projects_agg": total_committed_agg,
        "total_external_to_projects_agg": total_external_agg,
        "dashboard_data": dashboard_data,
        "assigned_data_json": assigned_data_json,
        "committed_internal_data_json": internal_committed_data_json,
        "committed_external_data_json": external_data_json,
        "unallocated_data_json": unallocated_data_json,
        "unallocated_data_raw_json": unallocated_data_raw_json,
    }

def _get_college_dashboard_data(user, fiscal_year):
    from django.db.models.functions import Coalesce, TruncMonth
    from django.db.models import Q, Sum, Value, DecimalField
    from decimal import Decimal
    import json
    
    def get_current_fiscal_year():
        from django.utils import timezone
        return str(timezone.now().year)


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

    year_int = int(fiscal_year)
    total_assigned = college_budget.total_assigned

    projects_current_year = Project.objects.filter(
        Q(internal_budget__gt=0) | Q(external_budget__gt=0), 
        
        # Followed by keyword arguments
        project_leader__college=user_college, 
        start_date__year=year_int,           
    ).select_related('project_leader').order_by('title')

    project_list = []
    total_committed_internal = Decimal('0.0')
    total_committed_external = Decimal('0.0')

    # Aggregate totals for the static cards
    for project in projects_current_year:
        assigned = project.internal_budget or Decimal('0')
        external = project.external_budget or Decimal('0')

        total_committed_internal += assigned
        total_committed_external += external

        project_list.append({
            'id': project.id,
            'title': project.title,
            'status': project.get_status_display(),
            'internal_funding_committed': assigned,
            'external_funding_committed': external,
        })
    
    uncommitted_remaining = total_assigned - total_committed_internal

    # --- Denominators for normalization ---
    norm_denominator_internal = total_assigned if total_assigned > 0 else Decimal('1') 
    norm_denominator_external = total_committed_external if total_committed_external > 0 else Decimal('1') 

    # --- Setup for Monthly Aggregation ---
    
    # 1. Internal Committed Data (Monthly Aggregation)
    project_internal_monthly = projects_current_year.filter(
        internal_budget__gt=0
    ).annotate(
        month=TruncMonth('start_date')
    ).values('month').annotate(
        monthly_commitment=Sum('internal_budget')
    ).order_by('month')

    internal_monthly_commitments = {i: Decimal('0') for i in range(1, 13)}
    for item in project_internal_monthly:
        internal_monthly_commitments[item['month'].month] += item['monthly_commitment']

    # --- 2. Assigned Budget History (For Initial & Remaining Charts) ---
    assigned_history_qs = BudgetHistory.objects.filter(
        college_budget__college=user_college,
        timestamp__year=year_int,
        action__in=['ALLOCATED', 'ADJUSTED']
    )

    monthly_assigned_changes = assigned_history_qs.annotate(
        month=TruncMonth('timestamp')
    ).values('month').annotate(
        net_change=Sum('amount')
    ).order_by('month')

    monthly_assigned_cuts = {i: Decimal('0') for i in range(1, 13)}
    for item in monthly_assigned_changes:
        monthly_assigned_cuts[item['month'].month] = item['net_change']

    # --- CHART DATA GENERATION ---

    # A. Initial Budget Chart Data (Cumulative Allocation Process - starts at zero)
    assigned_cumulatives_college = []
    running_total_assigned = Decimal('0')
    for month in range(1, 13):
        running_total_assigned += monthly_assigned_cuts[month]
        normalized_value = (running_total_assigned / norm_denominator_internal) * 100
        normalized_value = min(100, max(0, int(normalized_value)))
        assigned_cumulatives_college.append(int(normalized_value))
    
    # B. Internal Committed Chart Data (Normalized)
    internal_cumulative_data = []
    running_total_committed = Decimal('0')
    for month in range(1, 13):
        running_total_committed += internal_monthly_commitments.get(month, Decimal('0'))
        normalized_value = (running_total_committed / norm_denominator_internal) * 100
        normalized_value = min(100, max(0, int(normalized_value)))
        internal_cumulative_data.append(int(normalized_value))
        
    college_committed_data_json = json.dumps(internal_cumulative_data)

    # C. External Committed Chart Data (Normalized)
    project_external_monthly = projects_current_year.filter(
        external_budget__gt=0
    ).annotate(
        month=TruncMonth('start_date')
    ).values('month').annotate(
        monthly_commitment=Sum('external_budget')
    ).order_by('month')
    
    external_monthly_commitments = {i: Decimal('0') for i in range(1, 13)}
    for item in project_external_monthly:
        external_monthly_commitments[item['month'].month] += item['monthly_commitment']

    external_cumulative_data = []
    running_total_external = Decimal('0')

    for month in range(1, 13):
        running_total_external += external_monthly_commitments.get(month, Decimal('0'))
        normalized_value = (running_total_external / norm_denominator_external) * 100
        normalized_value = min(100, max(0, int(normalized_value)))
        external_cumulative_data.append(int(normalized_value))

    college_external_data_json = json.dumps(external_cumulative_data)

    # D. Monthly Remaining Funds Data (Normalized: Assigned - Committed)
    remaining_cumulative_data = []
    running_total_assigned_temp = Decimal('0')
    running_total_committed_temp = Decimal('0')

    for month in range(1, 13):
        running_total_assigned_temp += monthly_assigned_cuts.get(month, Decimal('0'))
        running_total_committed_temp += internal_monthly_commitments.get(month, Decimal('0'))
        
        uncommitted_value = running_total_assigned_temp - running_total_committed_temp
        
        normalized_value = (uncommitted_value / norm_denominator_internal) * 100
        normalized_value = int(normalized_value) # Allow negative values for deficit
        remaining_cumulative_data.append(normalized_value)

    college_remaining_data_json = json.dumps(remaining_cumulative_data)


    return {
        'is_setup': True,
        'college_budget': college_budget,
        'college_name': user_college.name,
        'total_assigned_original_cut': total_assigned,
        'total_committed_to_projects': total_committed_internal,
        'total_external_to_projects': total_committed_external,
        'uncommitted_remaining': uncommitted_remaining,
        'dashboard_data': project_list,
        
        # Chart Data
        'college_committed_data_json': college_committed_data_json, 
        'college_external_data_json': college_external_data_json,
        'college_remaining_data_json': college_remaining_data_json,
        'total_assigned_original_cut_norm': json.dumps(assigned_cumulatives_college)
    }

def _get_faculty_dashboard_data(user):
    # Retrieve ALL committed projects for the faculty member for the static card totals.
    user_projects = Project.objects.filter(
        Q(project_leader=user) | Q(providers=user)
    ).filter(
        Q(internal_budget__gt=0) | Q(external_budget__gt=0)
    ).distinct().select_related('project_leader__college').order_by('title')

    project_data = []
    total_internal = Decimal('0')
    total_external = Decimal('0')

    # Aggregate totals for the cards
    for project in user_projects:
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
    
    current_year = get_current_fiscal_year()
    year_int = int(current_year)
    total_assigned = total_internal + total_external

    # --- Denominators for normalization (Use 1 to prevent division by zero) ---
    norm_denom_internal = total_internal if total_internal > 0 else Decimal('1') 
    norm_denom_external = total_external if total_external > 0 else Decimal('1') 
    norm_denom_total = total_assigned if total_assigned > 0 else Decimal('1')

    # --- Internal Funding Chart (Monthly Aggregation) ---
    # QUERY: Filter only projects relevant to the current fiscal year for the monthly chart data.
    project_internal_monthly = Project.objects.filter(
        Q(project_leader=user) | Q(providers=user),
        internal_budget__gt=0,
        start_date__year=year_int  # ✅ Critical: Limit chart data points to the current fiscal year
    ).annotate(
        month=TruncMonth('start_date')
    ).values('month').annotate(monthly_commitment=Sum('internal_budget')).order_by('month')

    internal_monthly_commitments = {i: Decimal('0') for i in range(1, 13)}
    for item in project_internal_monthly:
        month_num = item['month'].month
        internal_monthly_commitments[month_num] += item['monthly_commitment']

    internal_cumulative_data = []
    running_total_internal = Decimal('0')
    for month in range(1, 13):
        running_total_internal += internal_monthly_commitments[month]
        normalized_value = (running_total_internal / norm_denom_internal) * 100
        normalized_value = min(100, max(0, int(normalized_value)))
        internal_cumulative_data.append(int(normalized_value))
        
    faculty_internal_data_json = json.dumps(internal_cumulative_data)
    
    # --- External Funding Chart (Monthly Aggregation) ---
    project_external_monthly = Project.objects.filter(
        Q(project_leader=user) | Q(providers=user),
        external_budget__gt=0,
        start_date__year=year_int  # ✅ Critical: Limit chart data points to the current fiscal year
    ).annotate(
        month=TruncMonth('start_date')
    ).values('month').annotate(monthly_commitment=Sum('external_budget')).order_by('month')

    external_monthly_commitments = {i: Decimal('0') for i in range(1, 13)}
    for item in project_external_monthly:
        month_num = item['month'].month
        external_monthly_commitments[month_num] += item['monthly_commitment']

    external_cumulative_data = []
    running_total_external = Decimal('0')
    for month in range(1, 13):
        running_total_external += external_monthly_commitments[month]
        normalized_value = (running_total_external / norm_denom_external) * 100
        normalized_value = min(100, max(0, int(normalized_value)))
        external_cumulative_data.append(int(normalized_value))
        
    faculty_external_data_json = json.dumps(external_cumulative_data)

    # --- Total Project Funding Chart (Internal + External) ---
    total_cumulative_data = []
    running_total_combined = Decimal('0')
    for month in range(1, 13):
        # NOTE: Using internal_monthly_commitments and external_monthly_commitments ensures we only sum data points for the current fiscal year.
        combined_monthly = internal_monthly_commitments[month] + external_monthly_commitments[month]
        running_total_combined += combined_monthly
        normalized_value = (running_total_combined / norm_denom_total) * 100
        normalized_value = min(100, max(0, int(normalized_value)))
        total_cumulative_data.append(int(normalized_value))

    faculty_total_data_json = json.dumps(total_cumulative_data)

    return {
        "is_setup": True,
        "dashboard_data": project_data,
        "total_internal": total_internal,
        "total_external": total_external,
        "total_assigned": total_assigned,
        "faculty_internal_data_json": faculty_internal_data_json,
        "faculty_external_data_json": faculty_external_data_json,
        "faculty_total_data_json": faculty_total_data_json,
    }

def _get_edit_page_data(user, fiscal_year):
    user_role = getattr(user, 'role', None)
    context = {}

    if user_role in ["VP", "DIRECTOR", "UESO"]:
        admin_data = _get_admin_dashboard_data(fiscal_year)
        context['colleges_data'] = admin_data['dashboard_data']
        context['allocation_map'] = json.dumps({
            item['college_id']: str(item['original_cut']) if item['original_cut'] > Decimal('0') else ''
            for item in admin_data['dashboard_data']
        })

    # The college admin edit view is removed, but we still need the data for the read-only dashboard
    college_roles = ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]
    if user_role in college_roles:
        college_data = _get_college_dashboard_data(user, fiscal_year)
        context.update(college_data)
        
    # Faculty data needs to be fetched if the edit view logic is extended for them
    faculty_roles = ["FACULTY", "IMPLEMENTER"]
    if user_role in faculty_roles:
         # Note: This is usually not called by edit_budget_view, but included for completeness if needed.
        faculty_data = _get_faculty_dashboard_data(user) 
        context.update(faculty_data)

    return context


@transaction.atomic
def _set_annual_budget_pool(user, fiscal_year, total_available):

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

    if commitment_delta == 0:
        return project

    current_committed_total = Project.objects.filter(
        project_leader__college=college_budget.college,
        start_date__year=int(fiscal_year)
    ).exclude(id=project.id).aggregate(
        total=Coalesce(Sum('internal_budget'), Value(Decimal('0.0')))
    )['total']

    new_total_commitment = current_committed_total + new_internal_budget

    if new_total_commitment > college_budget.total_assigned:
        raise ValueError(f"Assignment exceeds remaining college budget. College has ₱{college_budget.total_assigned - current_committed_total:,.2f} remaining.")

    project.internal_budget = new_internal_budget
    project.save(update_fields=['internal_budget'])

    college_budget.total_committed_to_projects = new_total_commitment
    college_budget.save(update_fields=['total_committed_to_projects'])

    if old_budget == Decimal('0.00'):
        action_type = 'ALLOCATED'
        description_str = f'Project "{project.title}" internal budget allocated: ₱{new_internal_budget:,.2f}.'
    else:
        action_type = 'ADJUSTED'
        description_str = f'Project "{project.title}" internal budget adjusted: ₱{old_budget:,.2f} → ₱{new_internal_budget:,.2f}.'

    BudgetHistory.objects.create(
        college_budget=college_budget,
        action=action_type,
        amount=commitment_delta,
        description=f'Project "{project.title}" internal budget adjusted: ₱{old_budget:,.2f} → ₱{new_internal_budget:,.2f}. (Funded by {college_budget.college.name})',
        user=user
    )
    return project


@role_required(["FACULTY", "IMPLEMENTER"], require_confirmed=True)
def faculty_project_budget_view(request, pk):
    base_template = get_templates(request)
    project = get_object_or_404(Project, pk=pk)

    # Handle add expense POST
    if request.method == 'POST':
        title = request.POST.get('reason') or request.POST.get('title')
        notes = request.POST.get('notes')
        amount_raw = request.POST.get('amount')
        receipt = request.FILES.get('receipt')
        try:
            amount_val = Decimal(str(amount_raw))
        except Exception:
            amount_val = Decimal('0')
        if title and amount_val > 0:
            try:
                ProjectExpense.objects.create(
                    project=project,
                    title=title,
                    reason=notes,
                    amount=amount_val,
                    receipt=receipt,
                    created_by=request.user,
                )
                # Log history
                try:
                    BudgetHistory.objects.create(
                        action='SPENT',
                        amount=amount_val,
                        description=f'Expense recorded for {project.title}: ₱{amount_val:,.2f} - {title}',
                        user=request.user
                    )
                except Exception:
                    pass
            except Exception:
                pass
            return redirect('faculty_project_budget', pk=project.id)

    expenses_qs = ProjectExpense.objects.filter(project=project).order_by('-date_incurred', '-created_at')

    total_budget = (project.internal_budget or Decimal('0')) + (project.external_budget or Decimal('0'))
    spent_total = expenses_qs.aggregate(s=Sum('amount'))['s'] or Decimal('0')
    remaining_total = max(Decimal('0'), total_budget - spent_total)
    percent_remaining = int(round(((remaining_total / total_budget) * 100))) if total_budget else 0

    chart_data = {
        'labels': ['Remaining', 'Spent'],
        'data': [float(remaining_total), float(spent_total)],
        'colors': ['#16a34a', '#d1d5db']
    }

    return render(request, 'budget/faculty_project_budget.html', {
        'base_template': base_template,
        'project': project,
        'expenses': expenses_qs,
        'budget_total': total_budget,
        'spent_total': spent_total,
        'remaining_total': remaining_total,
        'percent_remaining': percent_remaining,
        'chart_data_json': json.dumps(chart_data),
    })

def get_templates(request):
    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"
    return base_template


@role_required(["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR", "FACULTY", "IMPLEMENTER"], require_confirmed=True)
def budget_view(request):

    current_year = get_current_fiscal_year()
    user_role = getattr(request.user, 'role', None)

    if user_role in ["VP", "DIRECTOR", "UESO"]:
        context = _get_admin_dashboard_data(current_year)
    elif user_role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        context = _get_college_dashboard_data(request.user, current_year)
    elif user_role in ["FACULTY", "IMPLEMENTER"]:
        context = _get_faculty_dashboard_data(request.user)
        # Build faculty dashboard extras expected by template
        user = request.user
        # Projects overview with percent remaining
        user_projects = Project.objects.filter(
            Q(project_leader=user) | Q(providers=user)
        ).distinct().order_by('-updated_at')

        projects_overview = []
        for p in user_projects:
            total_budget = (p.internal_budget or 0) + (p.external_budget or 0)
            spent_total = p.used_budget or 0
            remaining = float(total_budget) - float(spent_total)
            percent_remaining = 0
            if total_budget:
                try:
                    percent_remaining = int(round((remaining / float(total_budget)) * 100))
                except Exception:
                    percent_remaining = 0
            projects_overview.append({
                'id': p.id,
                'title': p.title,
                'last_updated': p.updated_at,
                'percent_remaining': max(0, min(100, percent_remaining)),
                'providers': [
                    {
                        'name': u.get_full_name() or u.username,
                        'avatar': getattr(u, 'profile_picture_or_initial', '')
                    } for u in list(p.providers.all())[:3]
                ]
            })
        context['projects_overview'] = projects_overview

        # Recent expenses logs across user's projects
        recent_expenses = ProjectExpense.objects.filter(project__in=user_projects).select_related('project').order_by('-created_at')[:10]
        context['recent_expenses'] = recent_expenses

        # College budget donut data
        current_budget_total = 0
        percent_less_mean = 0
        try:
            user_college = getattr(user, 'college', None)
            fiscal_year = get_current_fiscal_year()
            if user_college:
                cb = CollegeBudget.objects.filter(college=user_college, fiscal_year=fiscal_year, status='ACTIVE').first()
                if cb:
                    # Prefer the model's tracked commitment if present; otherwise compute
                    committed_internal = getattr(cb, 'total_committed_to_projects', None)
                    if committed_internal is None:
                        committed_internal = Project.objects.filter(
                            project_leader__college=user_college,
                            start_date__year=int(fiscal_year)
                        ).aggregate(s=Coalesce(Sum('internal_budget'), Value(Decimal('0.0'))))['s']
                    committed_internal = committed_internal or Decimal('0')
                    total_assigned = cb.total_assigned or Decimal('0')
                    remaining = max(Decimal('0'), total_assigned - committed_internal)
                    current_budget_total = remaining
                    context['chart_data_json'] = json.dumps({
                        'labels': ['Remaining', 'Committed'],
                        'data': [float(remaining), float(committed_internal)],
                        'colors': ['#16a34a', '#d1d5db']
                    })
                    # Minimal historical stub (optional)
                    context['historical_data_json'] = json.dumps({ 'labels': [], 'data': [], 'color': '#0f3ea3' })
                    context['has_college_budget'] = True
                else:
                    context['has_college_budget'] = False
        except Exception:
            context['has_college_budget'] = False
        context['current_budget_total'] = current_budget_total
        context['percent_less_mean'] = percent_less_mean
    else:
        context = {"is_setup": False, "error": "Invalid User Role"}

    context["latest_history"] = BudgetHistory.objects.all().order_by('-timestamp')[:5]

    # Initialize the base queryset for external projects
    external_projects_qs = Project.objects.filter(
        external_budget__gt=0,
        start_date__year=int(current_year)
    )

    # Apply filtering for Faculty/Implementer roles
    if user_role in ["FACULTY", "IMPLEMENTER"]:
        external_projects_qs = external_projects_qs.filter(
            Q(project_leader=request.user) | Q(providers=request.user)
        ).distinct() 

    context["latest_external_projects"] = external_projects_qs.order_by('-external_budget')[:5]
    context["base_template"] = get_templates(request)
    context["title"] = f"Budget Dashboard ({current_year})"
    context["user_role"] = user_role
    context["is_admin"] = user_role in ["VP", "DIRECTOR", "UESO"]
    context["is_college_admin"] = user_role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]

    if not context.get('is_setup', True):
        if context.get('user_role') in ["VP", "DIRECTOR", "UESO"]:
            messages.info(request, "Annual Budget Pool not initialized. Please set it up.")
            return redirect('budget_setup')

        college_context = context.get('college_name')
        if college_context:
            messages.info(request, f"Budget for {college_context} not yet allocated for {current_year}.")
            return render(request, 'budget/no_budget_setup.html', context)

        return render(request, 'budget/no_budget_setup.html', context)

    # Render template based on role: use dedicated faculty dashboard for Faculty/Implementer
    if user_role in ["FACULTY", "IMPLEMENTER"]:
        return render(request, 'budget/faculty_budget.html', context)
    return render(request, 'budget/budget.html', context)


@role_required(["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def edit_budget_view(request):

    current_year = get_current_fiscal_year()
    context = _get_edit_page_data(request.user, current_year)
    context["base_template"] = get_templates(request)
    context["title"] = "Edit Budget"

    user_role = getattr(request.user, 'role', None)
    context["user_role"] = user_role
    context["is_college_admin"] = user_role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]


    college_roles = ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]
    if user_role in college_roles:
        pass # No POST handling for College Admins

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

                        committed_amount = Project.objects.filter(
                            project_leader__college=college,
                            start_date__year=int(current_year)
                        ).aggregate(
                            total=Coalesce(Sum('internal_budget'), Value(Decimal('0.0')))
                        )['total']

                        if amount < committed_amount:
                            raise Exception(f"Cannot set {college.name} budget to ₱{amount:,.2f}. It already has ₱{committed_amount:,.2f} committed to projects.")

                        if not created and allocation.total_assigned != amount:
                            previous_assigned = allocation.total_assigned
                            allocation.total_assigned = amount
                            allocation.assigned_by = request.user
                            allocation.status = 'ACTIVE'
                            allocation.save(update_fields=['total_assigned', 'assigned_by', 'status'])

                            BudgetHistory.objects.create(
                                college_budget=allocation,
                                action='ADJUSTED',
                                amount=amount - previous_assigned,
                                description=f'College cut for {college.name} adjusted: ₱{previous_assigned:,.2f} → ₱{amount:,.2f}',
                                user=request.user
                            )
                        elif created:
                            BudgetHistory.objects.create(
                                college_budget=allocation,
                                action='ALLOCATED',
                                amount=amount,
                                description=f'Initial college cut allocated for {college.name}: ₱{amount:,.2f}',
                                user=request.user
                            )

                        colleges_updated += 1

                    messages.success(request, f'Successfully updated allocations for {colleges_updated} colleges.')
                    return redirect('budget_edit')

            except Exception as e:
                messages.error(request, f'An error occurred: {e}')
                return redirect('budget_edit')
    # --- FIX END ---
    
    return render(request, 'budget/edit_budget.html', context)


@role_required(["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"], require_confirmed=True)
def budget_history_view(request):

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


@role_required(["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR", "FACULTY", "IMPLEMENTER"], require_confirmed=True)
def external_sponsors_view(request):

    current_year = get_current_fiscal_year()

    project_queryset = Project.objects.filter(
        external_budget__gt=0,
        start_date__year=int(current_year)
    ).order_by('-start_date')

    paginator = Paginator(project_queryset, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        "page_obj": page_obj,
        "title": "Projects with External Funding",
        "base_template": get_templates(request)
    }
    return render(request, 'budget/external_sponsors.html', context)


@role_required(["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def setup_annual_budget(request):

    current_year = get_current_fiscal_year()
    current_pool = BudgetPool.objects.filter(fiscal_year=current_year).first()

    if request.method == 'POST':
        form = AnnualBudgetForm(request.POST)
        if form.is_valid():
            try:
                annual_total = form.cleaned_data['annual_total']
                if annual_total < Decimal('0.00'):
                    messages.error(request, "Annual budget cannot be negative.")
                else:
                    _set_annual_budget_pool(request.user, current_year, annual_total)
                    messages.success(request, f'Set annual budget for {current_year} to ₱{annual_total:,.2f}.')
                    return redirect('budget_dashboard')
            except Exception as e:
                messages.error(request, f'Error initializing budget: {e}')
    else:
        initial_data = {'fiscal_year': current_year}
        if current_pool:
            initial_data['annual_total'] = current_pool.total_available
            messages.info(request, f"Budget for {current_year} is already set to ₱{current_pool.total_available:,.2f}. You can adjust it here.")

        form = AnnualBudgetForm(initial=initial_data)

    return render(request, 'budget/setup_annual_budget.html', {
        "base_template": get_templates(request),
        "form": form,
        "title": "Set Up Annual Budget",
        "current_pool": current_pool
    })

@role_required(["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"], require_confirmed=True)
def view_college_projects(request, college_id):
    """
    Renders a list of projects for a specific College ID (used by VP/Admin).
    
    NOTE: In the final HTML/JS, the College Admin and Faculty tables should link directly 
    to the project detail page (e.g., /projects/detail/123/) using JavaScript, not this view.
    
    If this view is reached, it means the VP/Admin clicked a college row and wants to 
    see the projects under that college for the current fiscal year.
    """
    current_year = get_current_fiscal_year()
    college = get_object_or_404(College, id=college_id)

    projects = Project.objects.filter(
        project_leader__college=college,
        start_date__year=int(current_year)
    ).order_by('title')
    
    context = {
        "title": f"Projects Allocated to {college.name} ({current_year})",
        "college": college,
        "projects": projects,
        "base_template": get_templates(request)
    }
    
    return render(request, 'budget/college_projects_list.html', context)

@role_required(["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def export_budget_data_view(request):
    fiscal_year = get_current_fiscal_year()

    admin_data = _get_admin_dashboard_data(fiscal_year)
    college_budget_data = admin_data['dashboard_data']

    external_projects = Project.objects.filter(
        external_budget__gt=0,
        start_date__year=int(fiscal_year)
    ).select_related('project_leader__college').prefetch_related('externalfunding_set').order_by('project_leader__college__name', 'title')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="budget_export_{fiscal_year}.csv"'

    writer = csv.writer(response)

    writer.writerow(['--- COLLEGE BUDGET ALLOCATIONS ---'])
    writer.writerow(['College', 'Initial Budget (Original Cut)', 'Internal Budget (Committed)', 'External Budget (Committed)', 'Remaining (Uncommitted)'])

    for item in college_budget_data:
        writer.writerow([
            item['college_name'],
            f"₱{item['original_cut']:,.2f}",
            f"₱{item['committed_funding']:,.2f}",
            f"₱{item['external_funding']:,.2f}",
            f"₱{item['uncommitted_remaining']:,.2f}"
        ])

    writer.writerow([])
    writer.writerow([])

    writer.writerow(['--- PROJECTS WITH EXTERNAL FUNDING ---'])
    writer.writerow(['Project Title', 'College', 'External Budget', 'Sponsor Name'])

    for project in external_projects:
        sponsor_name = 'N/A'
        if external_funding := project.externalfunding_set.first():
            sponsor_name = external_funding.sponsor_name

        writer.writerow([
            project.title,
            project.project_leader.college.name if project.project_leader and project.project_leader.college else 'N/A',
            f"₱{project.external_budget:,.2f}",
            sponsor_name
        ])

    return response