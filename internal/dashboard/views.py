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


@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"], require_confirmed=True)
def dashboard_view(request):
    user_role = getattr(request.user, 'role', None)
    vpde_content = user_role in ["VP", "DIRECTOR"]

    pending_requests = ClientRequest.objects.filter(status='PENDING')
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
        'events_json': events_json, # ADDED: Event data for mini-calendar JS
    }

    return render(request, 'dashboard/dashboard.html', context)
    
from internal.submissions.models import Submission
from shared.projects.models import Project

from django.http import JsonResponse
from django.db.models import Count
from collections import OrderedDict
from internal.submissions.models import Submission
from datetime import datetime, timedelta 
from django.utils import timezone


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

