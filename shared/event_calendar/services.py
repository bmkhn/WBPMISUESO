import pytz
from datetime import datetime
from django.utils import timezone
from django.db import models
from .models import MeetingEvent
from system.users.models import User
from shared.projects.models import ProjectEvent, Project

def get_events_by_date(user, for_main_calendar_view=False):
    """
    Fetches MeetingEvents and ProjectEvents formatted for the calendar.
    Filters based on user role.
    If 'for_main_calendar_view' is True, it fetches all events for the
    initial page load's JSON dump, bypassing user-specific filters
    (as the calendar_view itself is role-restricted).
    
    If 'for_main_calendar_view' is False (default), it fetches events
    for the dynamic JSON endpoint, filtered by user role.
    """
    events_qs = MeetingEvent.objects.none()
    project_events_qs = ProjectEvent.objects.select_related('project').none()

    if for_main_calendar_view:
        # For calendar_view, load all events for the initial JSON blob
        events_qs = MeetingEvent.objects.all()
        project_events_qs = ProjectEvent.objects.select_related('project').filter(placeholder=False)
    else:
        # Logic from old events_json view for dynamic fetching
        if user.role in ['UESO', 'VP', 'DIRECTOR']:
            events_qs = MeetingEvent.objects.all()
            project_events_qs = ProjectEvent.objects.select_related('project').filter(placeholder=False)
        elif user.role in ['PROGRAM_HEAD', 'DEAN', 'COORDINATOR']:
            events_qs = MeetingEvent.objects.filter(participants=user)
            project_events_qs = ProjectEvent.objects.select_related('project').filter(
                project__project_leader__college=user.college,
                placeholder=False
            )
        elif user.role in ['FACULTY', 'IMPLEMENTER']:
            events_qs = MeetingEvent.objects.filter(participants=user)
            project_events_qs = ProjectEvent.objects.select_related('project').filter(
                (models.Q(project__project_leader=user) |
                models.Q(project__providers=user)),
                placeholder=False
            )
        else:
            events_qs = MeetingEvent.objects.none()
            project_events_qs = ProjectEvent.objects.select_related('project').none()

    events_by_date = {}

    # MeetingEvents
    for event in events_qs:
        local_dt = timezone.localtime(event.datetime)
        date_str = local_dt.strftime('%Y-%m-%d')
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        
        event_data = {
            'id': event.id,
            'type': 'meeting',
            'title': event.title,
            'description': event.description,
            'date': date_str,
            'time': local_dt.strftime('%H:%M'),
            'location': event.location,
            'notes': event.notes,
            'status': event.status,
            'participants': [str(u.id) for u in event.participants.all()],
            'participant_names': [u.get_full_name() or u.username for u in event.participants.all()],
            'created_by': str(event.created_by.id) if event.created_by else None,
        }
        
        events_by_date[date_str].append(event_data)

    # ProjectEvents
    for pevent in project_events_qs:
        local_dt = timezone.localtime(pevent.datetime)
        date_str = local_dt.strftime('%Y-%m-%d')
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append({
            'id': pevent.id,
            'type': 'project',
            'title': pevent.title,
            'description': pevent.description,
            'date': date_str,
            'time': local_dt.strftime('%H:%M'),
            'location': pevent.location,
            'notes': getattr(pevent, 'notes', ''),
            'status': pevent.status,
            'leader': pevent.project.project_leader.get_full_name() if pevent.project.project_leader else '',
            'provider_names': [u.get_full_name() or u.username for u in pevent.project.providers.all()],
            'project_id': pevent.project.id,
            'project_name': pevent.project.title if pevent.project else '',
        })
        
    return events_by_date

def _parse_and_localize_datetime(date_str, time_str):
    """Helper to parse date/time and localize to Asia/Manila."""
    dt_str = f"{date_str} {time_str}"
    naive_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    local_tz = pytz.timezone("Asia/Manila")
    aware_dt = local_tz.localize(naive_dt)
    return aware_dt

def create_meeting_event(data, user):
    """
    Creates a new MeetingEvent.
    'data' is a dictionary from the request.
    'user' is the request.user.
    """
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    date = data.get("date")
    time = data.get("time")
    location = data.get("location", "").strip()
    participants = data.get("participants", [])
    notes = data.get("notes", "")

    if not (title and description and date and time and location):
        return None, {"errors": "Missing required fields."}

    try:
        aware_dt = _parse_and_localize_datetime(date, time)

        meeting = MeetingEvent.objects.create(
            title=title,
            description=description,
            datetime=aware_dt,
            location=location,
            created_by=user,
            updated_by=user,
            notes=notes
        )

        participant_ids = set(data.get("participants", []))
        participant_ids.add(str(user.id))

        # Filter users based on the combined set of IDs
        if participant_ids:
            users = User.objects.filter(id__in=participant_ids)
            meeting.participants.set(users)
            
        meeting.save() 
        return meeting, None
    except Exception as e:
        return None, {"errors": str(e)}

def update_meeting_event(event, data, user):
    """
    Updates an existing MeetingEvent.
    'event' is the MeetingEvent instance.
    'data' is a dictionary from the request.
    'user' is the request.user.
    """
    # Permission check
    allowed_roles = ["DIRECTOR", "UESO", "VP"]
    if not (user == event.created_by or user.role in allowed_roles):
        return None, {"errors": "Permission denied."}

    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    date = data.get("date")
    time = data.get("time")
    location = data.get("location", "").strip()
    participants = data.get("participants", [])
    notes = data.get("notes", "")

    if not (title and description and date and time and location):
        return None, {"errors": "Missing required fields."}

    try:
        aware_dt = _parse_and_localize_datetime(date, time)
        
        event.title = title
        event.description = description
        event.datetime = aware_dt
        event.location = location
        event.updated_by = user
        event.notes = notes
        event.save()
        
        if participants:
            users = User.objects.filter(id__in=participants)
            event.participants.set(users)
        else:
            event.participants.clear()
            
        return event, None
    except Exception as e:
        return None, {"errors": str(e)}

def delete_meeting_event(event, user):
    """
    Deletes an existing MeetingEvent.
    'event' is the MeetingEvent instance.
    'user' is the request.user.
    """
    # Permission check
    allowed_roles = ["DIRECTOR", "UESO", "VP"]
    if not (user == event.created_by or user.role in allowed_roles):
        return None, {"errors": "Permission denied."}
        
    try:
        event.delete()
        return True, None
    except Exception as e:
        return False, {"errors": str(e)}