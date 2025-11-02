from django.db.models import Count, Sum, F, Q, DecimalField
from django.db.models.functions import TruncMonth, TruncDay, TruncWeek, TruncYear
from datetime import datetime, date, timedelta
from django.utils import timezone
from decimal import Decimal

from shared.projects.models import Project, ProjectEvent
from internal.agenda.models import Agenda       
from shared.request.models import ClientRequest     
from internal.submissions.models import Submission
from system.users.models import User, College
from shared.budget.models import CollegeBudget # Added import

# Define active statuses (for use in other functions/charts)
ACTIVE_STATUSES = ['IN_PROGRESS', 'ON_HOLD']

# ==============================================================================
# CARD METRIC DATA FUNCTIONS (Unchanged)
# ==============================================================================

def get_total_projects_count(start_date, end_date):
    """
    FIX: Returns the count of projects that STARTED within the reporting date range.
    """
    count = Project.objects.filter(
        start_date__range=[start_date, end_date] 
    ).count()
    return {'metric': count}

def get_total_events_count(start_date, end_date):
    """Returns the total count of project events whose datetime is within the range."""
    count = ProjectEvent.objects.filter(datetime__range=[start_date, end_date]).count()
    return {'metric': count}

def get_total_providers_count(start_date, end_date):
    relevant_projects = Project.objects.filter(
        (Q(status__in=ACTIVE_STATUSES) | Q(estimated_end_date__range=[start_date, end_date])) &
        Q(start_date__lte=end_date)
    ).filter(
        project_leader__isnull=False
    ).distinct()

    leader_ids = relevant_projects.values_list('project_leader_id', flat=True).distinct()
    unique_leaders_count = len(leader_ids)

    college_ids = relevant_projects.filter(
        project_leader__college__isnull=False
    ).values_list('project_leader__college_id', flat=True).distinct()
    unique_colleges_count = len(college_ids)

    total_count = unique_colleges_count + unique_leaders_count

    return {'metric': total_count}

def get_total_individuals_trained(start_date, end_date):
    """
    Returns the SUM of `num_trained_individuals` from Submissions
    linked to ProjectEvents within the date range.
    """
    total_trained = Submission.objects.filter(
        event__datetime__range=[start_date, end_date], 
        num_trained_individuals__isnull=False   
    ).aggregate(
        total_trained=Sum('num_trained_individuals')
    )['total_trained'] or 0 

    return {'metric': total_trained}

# ==============================================================================
# CHART DATA FUNCTIONS 
# ==============================================================================

# --- MODIFIED HELPER: Returns the Django Trunc object AND the unit string ---
def _get_trunc_object(start_date, end_date):
    """
    Determines the appropriate Django Trunc function and the Chart.js unit string
    based on the date range duration.
    """
    try:
        # Ensure we are comparing date objects
        start_dt = start_date.date() if isinstance(start_date, datetime) else start_date
        end_dt = end_date.date() if isinstance(end_date, datetime) else end_date
        
        diff_days = (end_dt - start_dt).days

        if diff_days <= 31:
            return TruncDay, 'day' # < 1 month: Group by Day
        if diff_days <= 180:
            return TruncWeek, 'week' # < 6 months: Group by Week
        if diff_days <= 1095:
            return TruncMonth, 'month' # < 3 years: Group by Month
        return TruncYear, 'year' # > 3 years: Group by Year
    except Exception:
        return TruncMonth, 'month'


# --- MODIFIED FUNCTION: Returns timeUnit for JS ---
def get_active_projects_over_time(start_date, end_date):
    """
    Counts projects CREATED within the date range, grouped dynamically,
    and returns the grouping unit for chart axis scaling.
    """
    TruncFunc, time_unit = _get_trunc_object(start_date, end_date) # <-- GET UNIT HERE

    timescale_data = Project.objects.filter(
        created_at__range=[start_date, end_date]
    ).annotate(
        timescale_unit=TruncFunc('created_at')
    ).values('timescale_unit').annotate(
        count=Count('id')
    ).order_by('timescale_unit')

    data = [
        {
            "x": item['timescale_unit'].strftime('%Y-%m-%d'), 
            "y": item['count']
        } 
        for item in timescale_data
    ]

    # --- ADDED: Return the calculated time unit string ---
    return {'data': data, 'timeUnit': time_unit}


# --- MODIFIED FUNCTION: Returns timeUnit for JS ---
def get_trained_individuals_data(start_date, end_date):
    """
    Counts individuals trained within the date range, grouped dynamically,
    and returns the grouping unit for chart axis scaling.
    """
    TruncFunc, time_unit = _get_trunc_object(start_date, end_date) # <-- GET UNIT HERE

    timescale_data = Submission.objects.filter(
        event__datetime__range=[start_date, end_date],
        num_trained_individuals__isnull=False
    ).annotate(
        timescale_unit=TruncFunc('event__datetime')
    ).values('timescale_unit').annotate(
        total_trained=Sum('num_trained_individuals')
    ).order_by('timescale_unit')

    data = [
        {
            "x": item['timescale_unit'].strftime('%Y-%m-%d'),
            "y": item['total_trained'] or 0
        }
        for item in timescale_data
    ]
    
    # --- ADDED: Return the calculated time unit string ---
    return {'data': data, 'timeUnit': time_unit}

# --- Multi-Series Budget Functions (Unchanged from previous step) ---
def get_budget_multi_series_data(start_date, end_date):
    fiscal_year = str(end_date.year) 
    budget_queryset = CollegeBudget.objects.filter(fiscal_year=fiscal_year, status='ACTIVE').select_related('college').order_by('college__name')
    labels = []
    allotted_data = []
    committed_data = []
    unallocated_data = []
    
    COLORS = {
        "Allotted Budget (Total Cut)": "rgb(54, 162, 235)",
        "Committed to Projects (Internal Budget)": "rgb(255, 99, 132)",
        "Uncommitted Remaining (Available)": "rgb(75, 192, 192)",
    }
    
    for cb in budget_queryset:
        allotted = cb.total_assigned or Decimal('0')
        committed = cb.total_committed_to_projects 
        uncommitted = cb.uncommitted_remaining
        
        if allotted > Decimal('0') or committed > Decimal('0') or uncommitted != allotted:
            college_name = cb.college.name if cb.college else "Unassigned College"
            labels.append(college_name)
            allotted_data.append(float(allotted))
            committed_data.append(float(committed))
            unallocated_data.append(float(uncommitted))

    datasets = [
        {"label": "Allotted Budget (Total Cut)", "data": allotted_data, "backgroundColor": f"{COLORS['Allotted Budget (Total Cut)'].replace('rgb', 'rgba').replace(')', ', 0.66)')}", "borderColor": COLORS['Allotted Budget (Total Cut)'],},
        {"label": "Committed to Projects (Internal Budget)", "data": committed_data, "backgroundColor": f"{COLORS['Committed to Projects (Internal Budget)'].replace('rgb', 'rgba').replace(')', ', 0.66)')}", "borderColor": COLORS['Committed to Projects (Internal Budget)'], },
        {"label": "Uncommitted Remaining (Available)", "data": unallocated_data, "backgroundColor": f"{COLORS['Uncommitted Remaining (Available)'].replace('rgb', 'rgba').replace(')', ', 0.66)')}", "borderColor": COLORS['Uncommitted Remaining (Available)'],}
    ]

    return {"labels": labels, "datasets": datasets}

def get_budget_allocation_data(start_date, end_date):
    return get_budget_multi_series_data(start_date, end_date)


def get_agenda_distribution_data(start_date, end_date):
    agenda_data = Project.objects.filter((Q(status__in=ACTIVE_STATUSES) | Q(estimated_end_date__range=[start_date, end_date])) & Q(start_date__lte=end_date), agenda__isnull=False).values('agenda__name').annotate(count=Count('id')).order_by('-count')
    labels = [item['agenda__name'] for item in agenda_data]
    counts = [item['count'] for item in agenda_data]
    return {'labels': labels, 'counts': counts}


def get_request_status_distribution(start_date, end_date):
    requests = ClientRequest.objects.filter(submitted_at__range=[start_date, end_date])
    total_count = requests.count()
    if total_count == 0: return {'labels': ['Approved', 'Ongoing', 'Rejected'], 'approved_pct': 0, 'ongoing_pct': 0, 'rejected_pct': 0, 'total_count': 0}
    approved_count = requests.filter(status='APPROVED').count()
    rejected_count = requests.filter(status='REJECTED').count()
    ongoing_count = requests.exclude(Q(status='APPROVED') | Q(status='REJECTED')).count()
    approved_pct = round((approved_count / total_count) * 100, 1)
    rejected_pct = round((rejected_count / total_count) * 100, 1)
    ongoing_pct = round((ongoing_count / total_count) * 100, 1)
    current_sum = round(approved_pct + rejected_pct + ongoing_pct, 1)
    if current_sum != 100.0:
         diff = round(100.0 - current_sum, 1)
         if ongoing_count > 0: ongoing_pct = round(ongoing_pct + diff, 1)
         elif approved_count > 0: approved_pct = round(approved_pct + diff, 1)
         else: rejected_pct = round(rejected_pct + diff, 1)
    return {'labels': ['Approved', 'Ongoing', 'Rejected'], 'approved_pct': approved_pct, 'ongoing_pct': ongoing_pct, 'rejected_pct': rejected_pct, 'total_count': total_count}
    
def get_project_trends(start_date, end_date):
    current_duration = end_date.date() - start_date.date()
    previous_end_date = start_date - timedelta(days=1)
    previous_start_date = previous_end_date - current_duration
    current_tz = timezone.get_current_timezone()
    previous_start_dt = timezone.make_aware(datetime.combine(previous_start_date, datetime.min.time()), current_tz)
    previous_end_dt = timezone.make_aware(datetime.combine(previous_end_date, datetime.max.time()), current_tz)
    current_created_count = Project.objects.filter(created_at__range=[start_date, end_date]).count()
    previous_created_count = Project.objects.filter(created_at__range=[previous_start_dt, previous_end_dt]).count()
    created_change = 0
    created_trend = "flat"
    if previous_created_count > 0:
        created_change = round(((current_created_count - previous_created_count) / previous_created_count) * 100)
        if created_change > 0: created_trend = "up"
        elif created_change < 0: created_trend = "down"
    elif current_created_count > 0: created_change = 100; created_trend = "up"
    current_completed_count = Project.objects.filter(estimated_end_date__range=[start_date, end_date]).count()
    previous_completed_count = Project.objects.filter(estimated_end_date__range=[previous_start_dt, previous_end_dt]).count()
    completed_change = 0
    completed_trend = "flat"
    if previous_completed_count > 0:
        completed_change = round(((current_completed_count - previous_completed_count) / previous_completed_count) * 100)
        if created_change > 0: completed_trend = "up"
        elif created_change < 0: completed_trend = "down"
    elif current_completed_count > 0: completed_change = 100; completed_trend = "up"
    return {'created': {'number': current_created_count, 'change': created_change, 'trend': created_trend}, 'completed': {'number': current_completed_count, 'change': completed_change, 'trend': completed_trend}}