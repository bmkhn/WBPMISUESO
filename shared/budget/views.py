from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator
from decimal import Decimal
import json
import time
from system.users.decorators import role_required
from .models import (
    BudgetAllocation, BudgetCategory, ExternalFunding, 
    BudgetHistory, BudgetTemplate, BudgetPool
)
from .forms import BudgetAllocationEditForm, ExternalFundingEditForm, BudgetSearchForm
from system.users.models import College
from shared.projects.models import Project


def get_role_constants():
    INTERNAL_ROLES = ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]
    INTERNAL_WITH_COLLEGE_ROLES = ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]
    FACULTY_ROLES = ["FACULTY", "IMPLEMENTER"]
    return INTERNAL_ROLES, INTERNAL_WITH_COLLEGE_ROLES, FACULTY_ROLES

def get_templates(request):
    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"
    return base_template

def get_budget_context_data(request):
    """Get dynamic budget data based on user role"""
    user_role = getattr(request.user, 'role', None)
    current_year = timezone.now().year
    current_quarter = f"Q{((timezone.now().month - 1) // 3) + 1}-{current_year}"
    
    # Get template configuration for the role
    try:
        template_config = BudgetTemplate.objects.get(role=user_role, is_active=True)
    except BudgetTemplate.DoesNotExist:
        template_config = None
    
    # Base context data
    context = {
        "base_template": get_templates(request),
        "template_config": template_config,
        "current_quarter": current_quarter,
        "current_year": current_year,
        "title": "Budget Dashboard",
    }
    
    # Get budget allocations based on role
    if user_role in ["VP", "DIRECTOR"]:
        # VP and Director see all budget allocations
        budget_allocations = BudgetAllocation.objects.filter(
            status='ACTIVE',
            fiscal_year=str(current_year)
        ).select_related('college', 'project', 'category')
        
        # Overall budget statistics
        total_assigned = budget_allocations.aggregate(Sum('total_assigned'))['total_assigned__sum'] or Decimal('0')
        total_spent = budget_allocations.aggregate(Sum('total_spent'))['total_spent__sum'] or Decimal('0')
        
        # Use budget pool logic for consistent remaining calculation
        budget_pool, created = BudgetPool.objects.get_or_create(
            quarter=current_quarter,
            fiscal_year=str(current_year),
            defaults={'total_available': Decimal('10000000')}  # Default ₱10M budget pool
        )
        
        # Calculate remaining based on current quarter allocations only
        current_quarter_allocated = BudgetAllocation.objects.filter(
            fiscal_year=str(current_year),
            quarter=current_quarter,
            status='ACTIVE'
        ).aggregate(total=Sum('total_assigned'))['total'] or Decimal('0')
        
        total_remaining = budget_pool.total_available - current_quarter_allocated
        
        # Historical data (last 3 years for better comparison)
        historical_years = [str(current_year - 1), str(current_year - 2), str(current_year - 3)]
        historical_allocations = BudgetAllocation.objects.filter(
            fiscal_year__in=historical_years
        ).aggregate(
            avg_assigned=Avg('total_assigned'),
            avg_spent=Avg('total_spent'),
            total_assigned=Sum('total_assigned'),
            count=Count('id')
        )
        
        historical_avg = historical_allocations['avg_assigned'] or Decimal('0')
        historical_total = historical_allocations['total_assigned'] or Decimal('0')
        historical_count = historical_allocations['count'] or 0
        
        # Calculate comparison percentage
        current_vs_historical = 0
        historical_comparison_text = "No historical data available"
        
        if historical_avg > 0 and historical_count > 0:
            # Calculate percentage difference
            percentage_diff = ((float(total_assigned) - float(historical_avg)) / float(historical_avg)) * 100
            current_vs_historical = round(percentage_diff, 1)
            
            # Determine comparison text
            if abs(current_vs_historical) < 1:
                historical_comparison_text = "approximately the same as"
            elif current_vs_historical > 0:
                historical_comparison_text = f"{abs(current_vs_historical):.1f}% more than"
            else:
                historical_comparison_text = f"{abs(current_vs_historical):.1f}% less than"
            
            historical_comparison_text += " historical average"
        elif historical_total > 0:
            # Fallback to total comparison if average is 0 but total exists
            percentage_diff = ((float(total_assigned) - float(historical_total)) / float(historical_total)) * 100
            current_vs_historical = round(percentage_diff, 1)
            
            if abs(current_vs_historical) < 1:
                historical_comparison_text = "approximately the same as"
            elif current_vs_historical > 0:
                historical_comparison_text = f"{abs(current_vs_historical):.1f}% more than"
            else:
                historical_comparison_text = f"{abs(current_vs_historical):.1f}% less than"
            
            historical_comparison_text += " historical total"
        
        context.update({
            "budget_allocations": budget_allocations,
            "total_assigned": total_assigned,
            "total_spent": total_spent,
            "total_remaining": total_remaining,
            "budget_pool": budget_pool,
            "current_quarter_allocated": current_quarter_allocated,
            "utilization_percentage": round((total_spent / total_assigned * 100) if total_assigned > 0 else 0, 2),
            "historical_avg": historical_avg,
            "current_vs_historical": current_vs_historical,
            "historical_comparison_text": historical_comparison_text,
            "total_allocations_count": budget_allocations.count(),
            "active_colleges_count": budget_allocations.values('college').distinct().count(),
        })
        
    elif user_role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        # College-specific users see only their college's budgets
        user_college = getattr(request.user, 'college', None)
        if user_college:
            budget_allocations = BudgetAllocation.objects.filter(
                college=user_college,
                status='ACTIVE',
                fiscal_year=str(current_year)
            ).select_related('college', 'project', 'category')
            
            total_assigned = budget_allocations.aggregate(Sum('total_assigned'))['total_assigned__sum'] or Decimal('0')
            total_spent = budget_allocations.aggregate(Sum('total_spent'))['total_spent__sum'] or Decimal('0')
            total_remaining = budget_allocations.aggregate(Sum('total_remaining'))['total_remaining__sum'] or Decimal('0')
            
            context.update({
                "budget_allocations": budget_allocations,
                "total_assigned": total_assigned,
                "total_spent": total_spent,
                "total_remaining": total_remaining,
                "utilization_percentage": round((total_spent / total_assigned * 100) if total_assigned > 0 else 0, 2),
                "user_college": user_college,
            })
    
    elif user_role in ["FACULTY", "IMPLEMENTER"]:
        # Faculty see project budgets they're involved in
        user_projects = Project.objects.filter(
            project_leader=request.user
        ) | Project.objects.filter(
            providers=request.user
        )
        
        budget_allocations = BudgetAllocation.objects.filter(
            project__in=user_projects,
            status='ACTIVE',
            fiscal_year=str(current_year)
        ).select_related('college', 'project', 'category')
        
        total_assigned = budget_allocations.aggregate(Sum('total_assigned'))['total_assigned__sum'] or Decimal('0')
        total_spent = budget_allocations.aggregate(Sum('total_spent'))['total_spent__sum'] or Decimal('0')
        total_remaining = budget_allocations.aggregate(Sum('total_remaining'))['total_remaining__sum'] or Decimal('0')
        
        context.update({
            "budget_allocations": budget_allocations,
            "total_assigned": total_assigned,
            "total_spent": total_spent,
            "total_remaining": total_remaining,
            "utilization_percentage": round((total_spent / total_assigned * 100) if total_assigned > 0 else 0, 2),
            "user_projects": user_projects,
        })
    
    # External funding data (visible to all roles)
    external_fundings = ExternalFunding.objects.filter(
        status__in=['APPROVED', 'COMPLETED']
    ).select_related('project')
    
    context["external_fundings"] = external_fundings
    
    # Budget history (last 10 entries) - Only college budget allocations
    budget_history = BudgetHistory.objects.select_related(
        'user', 'budget_allocation', 'external_funding'
    ).filter(
        budget_allocation__isnull=False,  # Only budget allocation entries
        budget_allocation__college__isnull=False  # Only college allocations (not project allocations)
    ).order_by('-timestamp')[:10]
    
    context["budget_history"] = budget_history
    
    # Budget categories for filtering
    context["budget_categories"] = BudgetCategory.objects.all()
    
    # Chart data for JavaScript
    if user_role in ["VP", "DIRECTOR"]:
        # Prepare chart data for donut chart
        chart_data = {
            'labels': [],
            'data': [],
            'colors': ['#28a745', '#007bff', '#343a40', '#ffc107', '#dc3545', '#6f42c1', '#20c997', '#fd7e14']
        }
        
        # Get budget data by college
        college_budgets = budget_allocations.values('college__name').annotate(
            total_assigned=Sum('total_assigned')
        ).order_by('-total_assigned')[:5]
        
        for i, college in enumerate(college_budgets):
            if college['college__name']:
                chart_data['labels'].append(college['college__name'])
                chart_data['data'].append(float(college['total_assigned']))
        
        # If no college data, show project data
        if not chart_data['labels']:
            project_budgets = budget_allocations.values('project__title').annotate(
                total_assigned=Sum('total_assigned')
            ).order_by('-total_assigned')[:5]
            
            for i, project in enumerate(project_budgets):
                if project['project__title']:
                    chart_data['labels'].append(project['project__title'])
                    chart_data['data'].append(float(project['total_assigned']))
        
        # Add unassigned budget
        if total_assigned > 0:
            assigned_total = sum(chart_data['data'])
            unassigned = float(total_assigned) - assigned_total
            if unassigned > 0:
                chart_data['labels'].append('Unassigned')
                chart_data['data'].append(unassigned)
        
        # Historical data for line chart
        historical_data = {
            'labels': [],
            'data': [],
            'color': '#007bff'
        }
        
        # Get historical data for last 6 quarters
        from datetime import datetime, timedelta
        current_date = timezone.now()
        
        # Generate realistic historical data based on actual budget allocations
        quarters = []
        quarter_data = []
        
        for i in range(6):
            quarter_date = current_date - timedelta(days=90*i)
            quarter_label = f"Q{((quarter_date.month - 1) // 3) + 1}-{quarter_date.year}"
            quarters.append(quarter_label)
            
            # Get actual budget data for this quarter if it exists
            quarter_budget = budget_allocations.filter(
                quarter=quarter_label
            ).aggregate(total=Sum('total_assigned'))['total'] or 0
            
            # If no data for this quarter, generate realistic estimate based on current data
            if quarter_budget == 0 and i > 0:
                # Use current total with some variation for historical quarters
                variation = 0.8 + (i * 0.05)  # Slight increase over time
                quarter_budget = float(total_assigned) * variation
            
            quarter_data.append(float(quarter_budget) / 1000000)  # Convert to millions
        
        historical_data['labels'] = quarters[::-1]  # Reverse to show chronologically
        historical_data['data'] = quarter_data[::-1]
        
        # Convert to JSON
        context['chart_data_json'] = json.dumps(chart_data)
        context['historical_data_json'] = json.dumps(historical_data)
    
    return context


################################################################################################################################################################
@role_required(["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def budget_dispatcher(request):
    """Dispatch to appropriate budget view based on user role"""
    user_role = getattr(request.user, 'role', None)
    
    if user_role in ["VP", "DIRECTOR", "UESO"]:
        return budget_internal_view(request)
    elif user_role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        return budget_internal_college_view(request)
    elif user_role in ["FACULTY", "IMPLEMENTER"]:
        return budget_faculty_view(request)
    else:
        return budget_internal_view(request)

@role_required(["PROGRAM_HEAD", "DEAN", "COORDINATOR"], require_confirmed=True)
def budget_internal_college_view(request):
    context = get_budget_context_data(request)
    if context is None:
        context = {"title": "Budget Dashboard"}
    return render(request, 'budget/internal_budget.html', context)

@role_required(["FACULTY", "IMPLEMENTER"], require_confirmed=True)
def budget_faculty_view(request):
    context = get_budget_context_data(request)
    if context is None:
        context = {"title": "Budget Dashboard"}
    return render(request, 'budget/faculty_budget.html', context)

@role_required(["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def budget_internal_view(request):
    context = get_budget_context_data(request)
    
    # Ensure context is not None
    if context is None:
        context = {"title": "Budget Dashboard"}
    
    # Check if there's a custom template configuration
    template_config = context.get('template_config')
    if template_config and template_config.template_path:
        template_path = template_config.template_path
    else:
        # Default template based on role
        user_role = getattr(request.user, 'role', None)
        if user_role == "VP":
            template_path = 'budget/vp_budget.html'
        elif user_role == "DIRECTOR":
            template_path = 'budget/director_budget.html'
        else:
            template_path = 'budget/internal_budget.html'
    
    return render(request, template_path, context)


################################################################################################################################################################
@role_required(["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def budget_edit_dashboard(request):
    """Budget edit dashboard for Directors and VPs"""
    
    # Handle POST request for budget allocation updates
    if request.method == 'POST':
        current_year = timezone.now().year
        current_quarter = f"Q{((timezone.now().month - 1) // 3) + 1}-{current_year}"
        
        # Get default budget category (you may want to make this configurable)
        default_category = BudgetCategory.objects.first()
        if not default_category:
            messages.error(request, 'No budget category found. Please create a budget category first.')
            return redirect('budget_edit_dashboard')
        
        # Process college budget allocations
        colleges_updated = 0
        
        for key, value in request.POST.items():
            if key.startswith('college_') and value and float(value) > 0:
                college_id = key.replace('college_', '')
                try:
                    college = College.objects.get(id=college_id)
                    amount = Decimal(value)
                    
                    # Create or update budget allocation
                    allocation, created = BudgetAllocation.objects.get_or_create(
                        college=college,
                        category=default_category,
                        quarter=current_quarter,
                        fiscal_year=str(current_year),
                        defaults={
                            'total_assigned': amount,
                            'total_remaining': amount,
                            'total_spent': Decimal('0'),
                            'status': 'ACTIVE',
                            'assigned_by': request.user
                        }
                    )
                    
                    if not created:
                        # Update existing allocation
                        allocation.total_assigned = amount
                        allocation.total_remaining = amount - allocation.total_spent
                        allocation.assigned_by = request.user
                        allocation.save()
                    
                    # Only create history entry for NEW allocations (not updates)
                    if created:
                        # Add a small delay to ensure unique timestamps
                        time.sleep(0.1)  # 100ms delay between entries
                        
                        BudgetHistory.objects.create(
                            budget_allocation=allocation,
                            action='ALLOCATED',
                            amount=amount,
                            description=f'Budget allocated to {college.name}: ₱{amount:,.2f}',
                            user=request.user
                        )
                    
                    colleges_updated += 1
                    
                except College.DoesNotExist:
                    continue
                except (ValueError, TypeError):
                    continue
        
        if colleges_updated > 0:
            messages.success(request, f'Successfully updated budget allocations for {colleges_updated} colleges.')
        else:
            messages.warning(request, 'No budget allocations were updated.')
        
        return redirect('budget_edit_dashboard')
    
    # Get search parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    quarter_filter = request.GET.get('quarter', '')
    
    # Base queryset for budget allocations
    budget_queryset = BudgetAllocation.objects.select_related(
        'college', 'project', 'category'
    ).all()
    
    # Apply filters
    if search_query:
        budget_queryset = budget_queryset.filter(
            Q(college__name__icontains=search_query) |
            Q(project__title__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    if category_filter:
        budget_queryset = budget_queryset.filter(category_id=category_filter)
    
    if status_filter:
        budget_queryset = budget_queryset.filter(status=status_filter)
    
    if quarter_filter:
        budget_queryset = budget_queryset.filter(quarter=quarter_filter)
    
    # Pagination
    paginator = Paginator(budget_queryset, 10)
    page_number = request.GET.get('page')
    budget_allocations = paginator.get_page(page_number)
    
    # External funding queryset
    external_fundings = ExternalFunding.objects.select_related('project').filter(
        status__in=['APPROVED', 'COMPLETED', 'PENDING']
    )[:10]  # Limit to 10 for dashboard
    
    # Get colleges organized by campus
    tiniguiban_colleges = College.objects.filter(campus='TINIGUIBAN').order_by('name')
    external_colleges = College.objects.filter(campus='EXTERNAL').order_by('name')
    
    # Get current budget allocations for each college
    current_year = timezone.now().year
    current_quarter = f"Q{((timezone.now().month - 1) // 3) + 1}-{current_year}"
    
    # Create a dictionary of college allocations for easy lookup
    college_allocations = {}
    allocations = BudgetAllocation.objects.filter(
        fiscal_year=str(current_year),
        quarter=current_quarter,
        status='ACTIVE'
    ).select_related('college')
    
    for allocation in allocations:
        if allocation.college:
            college_allocations[allocation.college.id] = allocation.total_assigned
    
    # Calculate total remaining budget
    # Get or create budget pool for current quarter/year
    budget_pool, created = BudgetPool.objects.get_or_create(
        quarter=current_quarter,
        fiscal_year=str(current_year),
        defaults={'total_available': Decimal('10000000')}  # Default ₱10M budget pool
    )
    
    total_allocated = BudgetAllocation.objects.filter(
        fiscal_year=str(current_year),
        quarter=current_quarter,
        status='ACTIVE'
    ).aggregate(total=Sum('total_assigned'))['total'] or Decimal('0')
    
    total_remaining = budget_pool.total_available - total_allocated
    
    # Create search form
    search_form = BudgetSearchForm(initial={
        'search': search_query,
        'category': category_filter,
        'status': status_filter,
        'quarter': quarter_filter,
    })
    
    context = {
        "base_template": get_templates(request),
        "budget_allocations": budget_allocations,
        "external_fundings": external_fundings,
        "search_form": search_form,
        "total_allocations": budget_queryset.count(),
        "total_remaining": total_remaining,
        "total_allocated": total_allocated,
        "budget_pool": budget_pool,
        "tiniguiban_colleges": tiniguiban_colleges,
        "external_colleges": external_colleges,
        "college_allocations": college_allocations,
        "title": "Budget Management Dashboard",
    }
    
    return render(request, 'budget/director_edit_budget.html', context)

@role_required(["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def edit_budget_allocation(request, allocation_id):
    """Edit a specific budget allocation"""
    allocation = get_object_or_404(BudgetAllocation, id=allocation_id)
    
    if request.method == 'POST':
        form = BudgetAllocationEditForm(request.POST, instance=allocation)
        if form.is_valid():
            # Calculate remaining budget
            total_assigned = form.cleaned_data['total_assigned']
            total_spent = form.cleaned_data['total_spent']
            total_remaining = total_assigned - total_spent
            
            allocation = form.save(commit=False)
            allocation.total_remaining = total_remaining
            allocation.save()
            
            # Create history entry
            BudgetHistory.objects.create(
                budget_allocation=allocation,
                action='ADJUSTED',
                amount=total_assigned,
                description=f'Budget allocation updated by {request.user.get_full_name()}',
                user=request.user
            )
            
            messages.success(request, f'Budget allocation for {allocation} has been updated successfully.')
            return redirect('budget_edit_dashboard')
    else:
        form = BudgetAllocationEditForm(instance=allocation)
    
    context = {
        "base_template": get_templates(request),
        "form": form,
        "allocation": allocation,
        "title": f"Edit Budget Allocation - {allocation}",
    }
    
    return render(request, 'budget/edit_budget_allocation.html', context)

@role_required(["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def edit_external_funding(request, funding_id):
    """Edit external funding record"""
    funding = get_object_or_404(ExternalFunding, id=funding_id)
    
    if request.method == 'POST':
        form = ExternalFundingEditForm(request.POST, instance=funding)
        if form.is_valid():
            funding = form.save()
            
            # Create history entry
            BudgetHistory.objects.create(
                external_funding=funding,
                action='ADJUSTED',
                amount=funding.amount_offered,
                description=f'External funding updated by {request.user.get_full_name()}',
                user=request.user
            )
            
            messages.success(request, f'External funding for {funding.sponsor_name} has been updated successfully.')
            return redirect('budget_edit_dashboard')
    else:
        form = ExternalFundingEditForm(instance=funding)
    
    context = {
        "base_template": get_templates(request),
        "form": form,
        "funding": funding,
        "title": f"Edit External Funding - {funding.sponsor_name}",
    }
    
    return render(request, 'budget/edit_external_funding.html', context)

@role_required(["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def create_budget_allocation(request):
    """Create a new budget allocation"""
    if request.method == 'POST':
        form = BudgetAllocationEditForm(request.POST)
        if form.is_valid():
            # Calculate remaining budget
            total_assigned = form.cleaned_data['total_assigned']
            total_spent = form.cleaned_data['total_spent']
            total_remaining = total_assigned - total_spent
            
            allocation = form.save(commit=False)
            allocation.total_remaining = total_remaining
            allocation.assigned_by = request.user
            allocation.save()
            
            # Create history entry
            BudgetHistory.objects.create(
                budget_allocation=allocation,
                action='ALLOCATED',
                amount=total_assigned,
                description=f'New budget allocation created by {request.user.get_full_name()}',
                user=request.user
            )
            
            messages.success(request, f'New budget allocation has been created successfully.')
            return redirect('budget_edit_dashboard')
    else:
        form = BudgetAllocationEditForm()
    
    context = {
        "base_template": get_templates(request),
        "form": form,
        "title": "Create New Budget Allocation",
    }
    
    return render(request, 'budget/create_budget_allocation.html', context)

@role_required(["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def delete_budget_allocation(request, allocation_id):
    """Delete a budget allocation"""
    allocation = get_object_or_404(BudgetAllocation, id=allocation_id)
    
    if request.method == 'POST':
        # Create history entry before deletion
        BudgetHistory.objects.create(
            budget_allocation=allocation,
            action='ADJUSTED',
            amount=allocation.total_assigned,
            description=f'Budget allocation deleted by {request.user.get_full_name()}',
            user=request.user
        )
        
        allocation.delete()
        messages.success(request, f'Budget allocation for {allocation} has been deleted successfully.')
        return redirect('budget_edit_dashboard')
    
    context = {
        "base_template": get_templates(request),
        "allocation": allocation,
        "title": f"Delete Budget Allocation - {allocation}",
    }
    
    return render(request, 'budget/delete_budget_allocation.html', context)


@role_required(["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"], require_confirmed=True)
def budget_history_view(request):
    """Budget history view with search and filtering"""
    # Get search parameters
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort_by', 'datetime')
    order = request.GET.get('order', 'desc')
    date_filter = request.GET.get('date', '')
    
    # Base queryset - Only college budget allocations
    history_queryset = BudgetHistory.objects.select_related(
        'user', 'budget_allocation', 'external_funding'
    ).filter(
        budget_allocation__isnull=False,  # Only budget allocation entries
        budget_allocation__college__isnull=False  # Only college allocations (not project allocations)
    )
    
    # Apply search filter
    if search_query:
        history_queryset = history_queryset.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(action__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(budget_allocation__college__name__icontains=search_query)
        )
    
    # Apply date filter
    if date_filter:
        history_queryset = history_queryset.filter(timestamp__date=date_filter)
    
    # Apply sorting
    if sort_by == 'name':
        sort_field = 'user__first_name'
    elif sort_by == 'size':
        sort_field = 'amount'
    elif sort_by == 'date':
        sort_field = 'timestamp__date'
    else:  # datetime
        sort_field = 'timestamp'
    
    if order == 'asc':
        history_queryset = history_queryset.order_by(sort_field)
    else:
        history_queryset = history_queryset.order_by(f'-{sort_field}')
    
    # Pagination
    paginator = Paginator(history_queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Format history data for template
    history_data = []
    for history in page_obj:
        history_data.append({
            'user': f"{history.user.first_name} {history.user.last_name}" if history.user else "System",
            'action': history.action,  # Use raw action for amount formatting in template
            'subject': history.budget_allocation.college.name if history.budget_allocation and history.budget_allocation.college else "Unknown College",
            'datetime': history.timestamp.strftime("%b %d, %Y %H:%M"),  # Format like "Oct 28, 2025 01:38"
            'notes': history.description,
            'amount': history.amount,
        })
    
    context = {
        "base_template": get_templates(request),
        "history_data": history_data,
        "page_obj": page_obj,
        "search": search_query,
        "sort_by": sort_by,
        "order": order,
        "date": date_filter,
        "title": "Budget History",
    }
    
    return render(request, 'budget/budget-history.html', context)


@role_required(["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"], require_confirmed=True)
def budget_sponsor_view(request):
    """External sponsor/funding view with search and filtering"""
    # Get search parameters
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort_by', 'name')
    order = request.GET.get('order', 'asc')
    file_type = request.GET.get('file_type', '')
    date_filter = request.GET.get('date', '')
    
    # Base queryset
    sponsor_queryset = ExternalFunding.objects.select_related('project').filter(
        status__in=['APPROVED', 'COMPLETED', 'PENDING']
    )
    
    # Apply search filter
    if search_query:
        sponsor_queryset = sponsor_queryset.filter(
            Q(sponsor_name__icontains=search_query) |
            Q(project__title__icontains=search_query) |
            Q(project__description__icontains=search_query)
        )
    
    # Apply date filter
    if date_filter:
        sponsor_queryset = sponsor_queryset.filter(proposal_date__date=date_filter)
    
    # Apply sorting
    if sort_by == 'name':
        sort_field = 'sponsor_name'
    elif sort_by == 'file_type':
        sort_field = 'status'
    elif sort_by == 'size':
        sort_field = 'amount_offered'
    elif sort_by == 'date':
        sort_field = 'proposal_date'
    else:
        sort_field = 'sponsor_name'
    
    if order == 'asc':
        sponsor_queryset = sponsor_queryset.order_by(sort_field)
    else:
        sponsor_queryset = sponsor_queryset.order_by(f'-{sort_field}')
    
    # Pagination
    paginator = Paginator(sponsor_queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Format sponsor data for template
    sponsor_data = []
    for funding in page_obj:
        sponsor_data.append({
            'sponsor': funding.sponsor_name,
            'title': funding.project.title if funding.project else "No Project",
            'status': funding.get_status_display(),
            'total': funding.amount_offered,
            'spent': funding.amount_received,
            'remaining': funding.amount_offered - funding.amount_received,
            'completion_percentage': funding.completion_percentage,
        })
    
    context = {
        "base_template": get_templates(request),
        "sponsor_data": sponsor_data,
        "page_obj": page_obj,
        "search": search_query,
        "sort_by": sort_by,
        "order": order,
        "file_type": file_type,
        "date": date_filter,
        "title": "External Sponsors",
    }
    
    return render(request, 'budget/budget-sponsor.html', context)
