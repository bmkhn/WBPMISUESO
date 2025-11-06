from django.shortcuts import render
from shared.event_calendar.models import MeetingEvent
from shared.projects.models import Project, ProjectEvent
from system.users.decorators import role_required
from shared.request.models import ClientRequest
from system.users.views import User
from itertools import chain
import json

from shared.event_calendar import services 
from django.http import JsonResponse
from django.db.models import Count
from collections import OrderedDict
from internal.goals.models import Goal 
from internal.submissions.models import Submission
from datetime import datetime, timedelta 
from django.utils import timezone


def number_to_words_mock(num):
    if num == 100: return "ONE HUNDRED"
    
    words = [
        "ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE",
        "SIX", "SEVEN", "EIGHT", "NINE", "TEN",
        "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN",
        "SIXTEEN", "SEVENTEEN", "EIGHTEEN", "NINETEEN", "TWENTY"
    ]
    tens = ["", "", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY"]

    if num < 0 or num > 100: return str(num)
    if num < 20: return words[num]

    last_digit = num % 10
    tens_digit = num // 10

    return (tens[tens_digit] + (" " + words[last_digit] if last_digit != 0 else "")).strip()

# HELPER FUNCTION (Retained from previous fix)
def _count_matching_projects(goal: Goal) -> int:
    """Counts the number of projects that satisfy the Goal's filters."""
    qs = Project.objects.all()
    if goal.agenda_id:
        qs = qs.filter(agenda_id=goal.agenda_id)
    if goal.sdg_id:
        qs = qs.filter(sdgs=goal.sdg_id)
    if goal.project_status:
        qs = qs.filter(status=goal.project_status)
    return qs.count()

@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"], require_confirmed=True)
def dashboard_view(request):
    user_role = getattr(request.user, 'role', None)
    vpde_content = user_role in ["VP", "DIRECTOR"]

    pending_requests = ClientRequest.objects.filter(status__in=['RECEIVED', 'UNDER_REVIEW'])
    inprogress_projects = Project.objects.filter(status='IN_PROGRESS')
    expert_users = User.objects.filter(is_expert=True)

    all_events = list(chain(ProjectEvent.objects.filter(placeholder=False), MeetingEvent.objects.all()))
    events_in_calendar = len(all_events)
    

    projects = Project.objects.all().order_by('-updated_at')[:5]

    # Agenda Distribution Calculation
    from internal.agenda.models import Agenda
    all_projects = Project.objects.all()
    agenda_counts = {}
    for agenda in Agenda.objects.all():
        count = all_projects.filter(agenda=agenda).count()
        if count > 0:
            agenda_counts[agenda.name] = count
    
    
    # --- GOALS DATA GENERATION (FINAL FIX WITH CAP) ---
    goal_objects = Goal.objects.all() 
    
    dashboard_goals = []
    
    for goal in goal_objects:
        
        # Target value (Y/Denominator)
        target_value = getattr(goal, 'target_value', 1)
        display_target = target_value if target_value > 0 else 10 
        
        # Current value (Actual Count)
        current_count = _count_matching_projects(goal)
        
        # 1. Calculate progress percentage (0-100)
        progress = round((current_count / target_value) * 100) if target_value and target_value > 0 else 0
        progress = min(progress, 100) # Cap percentage at 100%

        # 2. Set current_qualifiers (Nominator)
        # FIX: Visually cap the nominator at the target_value (denominator)
        current_qualifiers = min(current_count, display_target)

        dashboard_goals.append({
            'id': goal.id,
            'title': goal.title,
            'progress': progress,
            'current_qualifiers': current_qualifiers, # CAPPED VALUE FOR DISPLAY
            'target_qualifiers': display_target,
            'target_words': number_to_words_mock(display_target).upper()
        })
    
    # 2. Sort the final list by the calculated 'progress' in Python (highest first)
    dashboard_goals.sort(key=lambda g: (g['progress'] >= 100, -g['progress']))
    # -----------------------------------------------------------------------
           
    # --- MIN-CALENDAR DATA GENERATION ---
    # Fetch events data structure used by the calendar app
    events_by_date = services.get_events_by_date(request.user, for_main_calendar_view=False)
    events_json = json.dumps(events_by_date)
    # ------------------------------------

    context = {
        'user_role': user_role,
        'vpde_content': vpde_content,
        'pending_requests': pending_requests,
        'inprogress_projects': inprogress_projects,
        'expert_users': expert_users,
        'events_in_calendar': events_in_calendar,
        'projects': projects,
        'agenda_distribution': agenda_counts,
        'events_json': events_json,
        'dashboard_goals': dashboard_goals,
    }

    return render(request, 'dashboard/dashboard.html', context)
    
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"], require_confirmed=True)
def get_submission_status_data(request):
    """
    Provides data for the Submission Status bar chart, filtered by date.
    """
    
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    
    # Get the current time zone from Django settings
    current_tz = timezone.get_current_timezone()

    if not end_str:
        # Default 'end' is the end of today (aware)
        end_date = timezone.now().replace(hour=23, minute=59, second=59)
    else:
        # Create an aware datetime for the *end* of the selected day
        dt = datetime.strptime(end_str, '%Y-%m-%d')
        end_date = timezone.make_aware(dt.replace(hour=23, minute=59, second=59), current_tz)
        
    if not start_str:
        # Default 'start' is 300 days ago, at the start of that day
        start_date = (end_date - timedelta(days=300)).replace(hour=0, minute=0, second=0)
    else:
        # Create an aware datetime for the *start* of the selected day
        dt = datetime.strptime(start_str, '%Y-%m-%d')
        start_date = timezone.make_aware(dt.replace(hour=0, minute=0, second=0), current_tz)

    # This query will now use time-zone-aware dates
    status_data = Submission.objects.filter(
        created_at__range=(start_date, end_date)
    ).values('status').annotate(count=Count('status')).order_by('status')
    
    status_choices = dict(Submission.SUBMISSION_STATUS_CHOICES)
    data_dict = OrderedDict((key, 0) for key, label in Submission.SUBMISSION_STATUS_CHOICES)
    
    for item in status_data:
        if item['status'] in data_dict:
            data_dict[item['status']] = item['count']
            
    labels = [status_choices.get(key, key) for key in data_dict.keys()]
    counts = list(data_dict.values())
    
    return JsonResponse({
        'labels': labels,
        'counts': counts,
    })

@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"], require_confirmed=True)
def get_project_status_data(request):
    """
    Provides data for the Project Status pie chart, filtered by date.
    """
    
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    current_tz = timezone.get_current_timezone()

    if not end_str:
        end_date = timezone.now().replace(hour=23, minute=59, second=59)
    else:
        dt = datetime.strptime(end_str, '%Y-%m-%d')
        end_date = timezone.make_aware(dt.replace(hour=23, minute=59, second=59), current_tz)
        
    if not start_str:
        start_date = (end_date - timedelta(days=300)).replace(hour=0, minute=0, second=0)
    else:
        dt = datetime.strptime(start_str, '%Y-%m-%d')
        start_date = timezone.make_aware(dt.replace(hour=0, minute=0, second=0), current_tz)

    # This query will now use time-zone-aware dates
    status_data = Project.objects.filter(
        created_at__range=(start_date, end_date)
    ).values('status').annotate(count=Count('status')).order_by('status')
    
    status_choices = dict(Project.STATUS_CHOICES)
    data_dict = OrderedDict((key, 0) for key, label in Project.STATUS_CHOICES)
    
    for item in status_data:
        if item['status'] in data_dict:
            data_dict[item['status']] = item['count']
            
    labels = [status_choices.get(key, key) for key in data_dict.keys()]
    counts = list(data_dict.values())
    
    return JsonResponse({
        'labels': labels,
        'counts': counts,
    })