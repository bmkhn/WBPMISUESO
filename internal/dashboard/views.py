from django.shortcuts import render
from shared.event_calendar.models import MeetingEvent
from shared.projects.models import Project, ProjectEvent
from system.users.decorators import role_required
from shared.request.models import ClientRequest
from system.users.views import User
from itertools import chain
import json

# Import the calendar service to fetch events
from shared.event_calendar import services 


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