from django.db.models import Count, Sum, F, Q, DecimalField
from django.db.models.functions import TruncMonth
from datetime import datetime, date
from django.utils import timezone

from shared.projects.models import Project, ProjectEvent
from internal.agenda.models import Agenda       
from shared.request.models import ClientRequest         
from system.users.models import User, College

# Define active statuses (for use in other functions/charts)
ACTIVE_STATUSES = ['IN_PROGRESS', 'ON_HOLD']

# ==============================================================================
# CARD METRIC DATA FUNCTIONS (All date-filtered)
# ==============================================================================

def get_total_projects_count(start_date, end_date):
    """
    FIX: Returns the count of projects that STARTED within the reporting date range.
    """
    count = Project.objects.filter(
        start_date__range=[start_date, end_date] # Counts projects whose start_date is in the period
    ).count()
    return {'metric': count}

def get_total_events_count(start_date, end_date):
    """Returns the total count of project events whose datetime is within the range."""
    count = ProjectEvent.objects.filter(datetime__range=[start_date, end_date]).count()
    return {'metric': count}

def get_total_providers_count(start_date, end_date):
    """
    FIX: Returns the count of UNIQUE Colleges/Providers involved in projects 
    that STARTED within the date range, to match the project count logic.
    """
    
    # 1. Filter Projects that started in the range.
    active_projects = Project.objects.filter(
        start_date__range=[start_date, end_date] # Use the same "started in range" filter
    )
    
    # 2. Get the distinct College IDs of all Users who are 'providers' in these projects.
    distinct_college_ids = active_projects.values_list(
        'providers__college', 
        flat=True
    ).exclude(providers__college__isnull=True).distinct()
    
    count = distinct_college_ids.count()
    return {'metric': count}

def get_total_trained_individuals_count(start_date, end_date):
    """Returns the count of unique Users confirmed/trained within the date range."""
    count = User.objects.filter(
        date_joined__range=[start_date, end_date],
        is_confirmed=True 
    ).count()
    return {'metric': count}

# ==============================================================================
# CHART DATA FUNCTIONS (All date-filtered)
# ==============================================================================

def get_active_projects_over_time(start_date, end_date):
    """
    Returns monthly counts for projects that started within the period 
    and are currently active.
    """
    # NOTE: Chart logic typically focuses on events/starts *within* the range.
    # To show project starts over time:
    active_projects_started_in_range = Project.objects.filter(
        start_date__range=[start_date, end_date],
        status__in=ACTIVE_STATUSES
    )
    
    monthly_counts = active_projects_started_in_range.annotate(
        month=TruncMonth('start_date')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    labels = [item['month'].strftime("%b %Y") for item in monthly_counts]
    data = [item['count'] for item in monthly_counts]

    return {
        'labels': labels, 
        'data': data,
        'label': 'Active Projects Started'
    }

def get_budget_allocation_data(start_date, end_date):
    """
    Returns budget allocation data for projects active within the date range,
    grouped by the month of the project's start date.
    """
    
    # Projects that started in the range and are currently active.
    projects = Project.objects.filter(
        start_date__range=[start_date, end_date],
        status__in=ACTIVE_STATUSES
    )
    
    budget_data = projects.annotate(
        period=TruncMonth('start_date')
    ).values('period').annotate(
        allocated=Sum(F('internal_budget') + F('external_budget'), output_field=DecimalField()), 
        
        used=Sum(F('used_budget'), output_field=DecimalField()) 
    ).order_by('period')

    labels = [item['period'].strftime("%b %Y") for item in budget_data]
    # Convert to Millions 
    allocated = [float(item['allocated'] or 0) / 1000000 for item in budget_data]
    used = [float(item['used'] or 0) / 1000000 for item in budget_data]
    remaining = [round(a - u, 2) for a, u in zip(allocated, used)]

    return {
        'labels': labels, 
        'allocated': allocated,
        'used': used,
        'remaining': remaining
    }

def get_agenda_distribution_data(start_date, end_date):
    """
    Returns agenda distribution data for a Pie Chart, filtered by ProjectEvent datetime.
    """
    
    # Uses correct 'datetime' field and correct traversal path (ProjectEvent -> Project -> Agenda)
    agenda_counts = ProjectEvent.objects.filter(
        datetime__range=[start_date, end_date], 
        project__agenda__isnull=False 
    ).values(
        'project__agenda__name'      
    ).annotate(
        count=Count('id')
    ).order_by('-count')

    labels = [item['project__agenda__name'] for item in agenda_counts] 
    data = [item['count'] for item in agenda_counts]

    return {
        'labels': labels, 
        'data': data,
    }

def get_trained_individuals_data(start_date, end_date):
    """Returns trained individuals data grouped by College/Provider for a Bar Chart."""
    
    college_user_counts = College.objects.filter(
        user__date_joined__range=[start_date, end_date],
        user__is_confirmed=True 
    ).annotate(
        user_count=Count('user', distinct=True)
    ).values('name', 'user_count').order_by('-user_count')
    
    labels = [item['name'] for item in college_user_counts]
    data = [item['user_count'] for item in college_user_counts]

    return {
        'labels': labels, 
        'data': data,
    }

def get_request_status_data(start_date, end_date):
    """
    Returns the percentage distribution and total count of ClientRequest statuses.
    """
    
    # Uses correct 'submitted_at' field for date filtering.
    requests = ClientRequest.objects.filter(
        submitted_at__range=[start_date, end_date] 
    )
    total_count = requests.count()

    if total_count == 0:
        return {
            'labels': ['Approved', 'Ongoing', 'Rejected'],
            'approved_pct': 0,
            'ongoing_pct': 0,
            'rejected_pct': 0,
            'total_count': 0 
        }

    approved_count = requests.filter(status='APPROVED').count()
    rejected_count = requests.filter(status='REJECTED').count()
    
    # Ongoing: All other statuses not explicitly APPROVED or REJECTED.
    ongoing_count = requests.exclude(
        Q(status='APPROVED') | Q(status='REJECTED')
    ).count()

    approved_pct = round((approved_count / total_count) * 100, 1)
    rejected_pct = round((rejected_count / total_count) * 100, 1)
    ongoing_pct = round((ongoing_count / total_count) * 100, 1)

    # Simple correction for rounding errors
    current_sum = round(approved_pct + rejected_pct + ongoing_pct, 1)
    if current_sum != 100.0:
        diff = 100.0 - current_sum
        ongoing_pct = round(ongoing_pct + diff, 1)
        
    return {
        'labels': ['Approved', 'Ongoing', 'Rejected'],
        'approved_pct': approved_pct,
        'ongoing_pct': ongoing_pct,
        'rejected_pct': rejected_pct,
        'total_count': total_count # Numerical count included
    }