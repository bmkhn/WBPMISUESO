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
from django.db.models import Count, Q
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

def _count_matching_projects(goal: Goal) -> int:
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
    user_college = getattr(request.user, 'college', None)
    
    show_admin_content = user_role in ["VP", "DIRECTOR", "UESO"]
    show_events_card = show_admin_content or user_role in ["COORDINATOR", "DEAN", "PROGRAM_HEAD"]

    pending_requests = ClientRequest.objects.filter(status__in=['RECEIVED', 'UNDER_REVIEW'])
    inprogress_projects = Project.objects.filter(status='IN_PROGRESS')
    expert_users = User.objects.filter(is_expert=True)

    projects = Project.objects.all().order_by('-updated_at')[:5]

    from internal.agenda.models import Agenda
    all_projects = Project.objects.all()
    agenda_counts = {}
    for agenda in Agenda.objects.all():
        count = all_projects.filter(agenda=agenda).count()
        if count > 0:
            agenda_counts[agenda.name] = count
    
    events_in_calendar = 0 
    now = timezone.now()
    
    if show_events_card:
        future_project_events = ProjectEvent.objects.filter(placeholder=False, datetime__gte=now)
        future_meeting_events = MeetingEvent.objects.filter(datetime__gte=now)
        
        if show_admin_content:
            all_events = list(chain(future_project_events, future_meeting_events))
        elif user_college:
            
            relevant_projects = Project.objects.filter(
                Q(project_leader__college=user_college) |
                Q(providers__college=user_college)
            ).distinct()
            
            filtered_project_events = future_project_events.filter(
                project__in=relevant_projects
            ).distinct()
            
            filtered_meeting_events = future_meeting_events.filter(
                participants__college=user_college
            ).distinct()
            
            all_events = list(chain(filtered_project_events, filtered_meeting_events))
        else:
            all_events = []
            
        events_in_calendar = len(all_events)
    
    goal_objects = Goal.objects.all() 
    
    dashboard_goals = []
    
    for goal in goal_objects:
        
        target_value = getattr(goal, 'target_value', 1)
        display_target = target_value if target_value > 0 else 10 
        
        current_count = _count_matching_projects(goal)
        
        progress = round((current_count / target_value) * 100) if target_value and target_value > 0 else 0
        progress = min(progress, 100)

        current_qualifiers = min(current_count, display_target)

        dashboard_goals.append({
            'id': goal.id,
            'title': goal.title,
            'progress': progress,
            'current_qualifiers': current_qualifiers,
            'target_qualifiers': display_target,
            'target_words': number_to_words_mock(display_target).upper()
        })
    
    dashboard_goals.sort(key=lambda g: (g['progress'] >= 100, -g['progress']))
           
    events_by_date = services.get_events_by_date(request.user, for_main_calendar_view=False)
    events_json = json.dumps(events_by_date)

    context = {
        'user_role': user_role,
        'vpde_content': show_admin_content,
        'pending_requests': pending_requests,
        'inprogress_projects': inprogress_projects,
        'expert_users': expert_users,
        'events_in_calendar': events_in_calendar,
        'projects': projects,
        'agenda_distribution': agenda_counts,
        'events_json': events_json,
        'dashboard_goals': dashboard_goals,
        'show_events_card': show_events_card,
    }

    return render(request, 'dashboard/dashboard.html', context)
    
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"], require_confirmed=True)
def get_submission_status_data(request):
    
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