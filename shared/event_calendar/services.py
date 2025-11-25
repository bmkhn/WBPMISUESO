import pytz
from datetime import datetime, date as date_class
from django.utils import timezone
from django.db import models
from .models import MeetingEvent
from system.users.models import User
from shared.projects.models import ProjectEvent, Project
from .holidays import get_philippine_holidays

def format_time_12hour(dt):
    """Convert datetime to 12-hour format string (h:MM AM/PM)"""
    if not dt:
        return 'N/A'
    local_dt = timezone.localtime(dt)
    hour = local_dt.hour
    minute = local_dt.minute
    period = 'PM' if hour >= 12 else 'AM'
    display_hour = 12 if hour == 0 or hour == 12 else (hour % 12)
    return f"{display_hour}:{minute:02d} {period}"

def get_events_by_date(user, for_main_calendar_view=False, include_holidays=True):
    """
    Fetches MeetingEvents, ProjectEvents, and Philippine holidays formatted for the calendar.
    Filters based on user role for consistent security across all user types.
    
    Args:
        user: The requesting user
        for_main_calendar_view: Deprecated - kept for backward compatibility, no longer used
        include_holidays: If True, includes Philippine holidays in the calendar
    
    Returns:
        dict: Events grouped by date {date_str: [event_dict, ...]}
    """
    events_qs = MeetingEvent.objects.none()
    project_events_qs = ProjectEvent.objects.select_related('project').none()

    # Apply role-based filtering for all requests to ensure consistent security
    # All user types see events filtered by their role permissions
    user_role = getattr(user, 'role', None)
    if user_role in ['UESO', 'VP', 'DIRECTOR']:
        events_qs = MeetingEvent.objects.all()
        project_events_qs = ProjectEvent.objects.select_related('project').filter(placeholder=False)
    elif user_role in ['PROGRAM_HEAD', 'DEAN', 'COORDINATOR']:
        events_qs = MeetingEvent.objects.filter(participants=user)
        project_events_qs = ProjectEvent.objects.select_related('project').filter(
            project__project_leader__college=user.college,
            placeholder=False
        )
    elif user_role in ['FACULTY', 'IMPLEMENTER']:
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
        
        end_time_str = None
        if event.end_datetime:
            end_local_dt = timezone.localtime(event.end_datetime)
            end_time_str = end_local_dt.strftime('%H:%M')
        
        event_data = {
            'id': event.id,
            'type': 'meeting',
            'title': event.title,
            'description': event.description,
            'date': date_str,
            'time': local_dt.strftime('%H:%M'),
            'end_time': end_time_str,
            'location': event.location,
            'notes': event.notes,
            'notes_attachment': event.notes_attachment.url if event.notes_attachment else None,
            'notes_attachment_name': event.notes_attachment.name.split('/')[-1] if event.notes_attachment else None,
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
    
    # Add Philippine holidays
    if include_holidays:
        # Get current year and next year holidays
        from datetime import datetime
        current_year = datetime.now().year
        
        for year in [current_year, current_year + 1]:
            holidays = get_philippine_holidays(year)
            for holiday_date, holiday_info in holidays.items():
                date_str = holiday_date.strftime('%Y-%m-%d')
                if date_str not in events_by_date:
                    events_by_date[date_str] = []
                
                # Add holiday as a special event type
                events_by_date[date_str].append({
                    'id': f'holiday-{date_str}',
                    'type': 'holiday',
                    'title': holiday_info['name'],
                    'description': f"Philippine {holiday_info['type'].capitalize()} Holiday",
                    'date': date_str,
                    'time': '00:00',
                    'holiday_type': holiday_info['type'],  # 'regular' or 'special'
                    'is_holiday': True,
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
    end_time = data.get("end_time")
    location = data.get("location", "").strip()
    participants = data.get("participants", [])
    notes = data.get("notes", "")
    notes_attachment = data.get("notes_attachment")  # File from request

    if not (title and description and date and time and location):
        return None, {"errors": "Missing required fields."}
    
    if not end_time:
        return None, {"errors": "End time is required."}

    try:
        aware_dt = _parse_and_localize_datetime(date, time)
        end_aware_dt = _parse_and_localize_datetime(date, end_time) if end_time else None
        
        # Validate end time is after start time
        if end_aware_dt and end_aware_dt <= aware_dt:
            return None, {"errors": "End time must be after start time."}
        
        # STEP 2: Time validation - Skip for VP/DIRECTOR/UESO, only check visible meetings for others
        # VP/DIRECTOR/UESO can schedule freely (they see all meetings anyway)
        user_role = getattr(user, 'role', None)
        if user_role not in ['VP', 'DIRECTOR', 'UESO']:
            # For PROGRAM_HEAD/DEAN/COORDINATOR/FACULTY/IMPLEMENTER
            # Only check meetings they can see (meetings where they are participants)
            overlapping_meetings = MeetingEvent.objects.filter(
                datetime__date=aware_dt.date(),
                participants=user  # Only check visible meetings (role-filtered)
            ).exclude(
                end_datetime__isnull=True  # Only check meetings with end_datetime
            ).exclude(
                # Exclude meetings that don't overlap
                models.Q(datetime__gte=end_aware_dt) |  # Existing meeting starts after new meeting ends
                models.Q(end_datetime__lte=aware_dt)   # Existing meeting ends before new meeting starts
            )
            
            if overlapping_meetings.exists():
                conflict = overlapping_meetings.first()
                conflict_time = format_time_12hour(conflict.datetime)
                conflict_end = format_time_12hour(conflict.end_datetime) if conflict.end_datetime else 'N/A'
                return None, {"errors": f"Time conflict! \"{conflict.title}\" is already scheduled from {conflict_time} to {conflict_end} on this date."}

        # Check for participant conflicts
        participant_ids = set(data.get("participants", []))
        participant_ids.add(str(user.id))
        
        if participant_ids:
            # Find meetings on the same date that overlap in time and have common participants
            conflicting_meetings = MeetingEvent.objects.filter(
                datetime__date=aware_dt.date(),
                participants__id__in=participant_ids
            ).exclude(
                end_datetime__isnull=True
            ).exclude(
                models.Q(datetime__gte=end_aware_dt) |
                models.Q(end_datetime__lte=aware_dt)
            ).distinct()
            
            if conflicting_meetings.exists():
                conflict = conflicting_meetings.first()
                conflict_time = format_time_12hour(conflict.datetime)
                conflict_end = format_time_12hour(conflict.end_datetime) if conflict.end_datetime else 'N/A'
                
                # Find which participants are conflicting by checking if they're in the conflict meeting's participants
                conflict_participant_ids = set(str(p.id) for p in conflict.participants.all())
                conflicting_ids = participant_ids.intersection(conflict_participant_ids)
                
                if conflicting_ids:
                    # Get the actual User objects for the conflicting participants
                    conflict_participants = User.objects.filter(id__in=conflicting_ids)
                    participant_names = [p.get_full_name() or p.username for p in conflict_participants]
                    if len(participant_names) == 1:
                        return None, {"errors": f"{participant_names[0]} is already scheduled in \"{conflict.title}\" from {conflict_time} to {conflict_end} on this date."}
                    else:
                        names_str = ", ".join(participant_names[:-1]) + f" and {participant_names[-1]}"
                        return None, {"errors": f"{names_str} are already scheduled in \"{conflict.title}\" from {conflict_time} to {conflict_end} on this date."}

        meeting = MeetingEvent.objects.create(
            title=title,
            description=description,
            datetime=aware_dt,
            end_datetime=end_aware_dt,
            location=location,
            created_by=user,
            updated_by=user,
            notes=notes,
            notes_attachment=notes_attachment if notes_attachment else None
        )

        # Filter users based on the combined set of IDs (participant_ids already set above)
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
    user_role = getattr(user, 'role', None)
    if not (user == event.created_by or user_role in allowed_roles):
        return None, {"errors": "Permission denied."}

    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    date = data.get("date")
    time = data.get("time", "").strip()
    end_time = data.get("end_time", "").strip()
    location = data.get("location", "").strip()
    participants = data.get("participants", [])
    notes = data.get("notes", "")
    notes_attachment = data.get("notes_attachment")  # File from request

    if not (title and description and date and time and location):
        return None, {"errors": "Missing required fields."}
    
    if not end_time:
        return None, {"errors": "End time is required."}

    try:
        aware_dt = _parse_and_localize_datetime(date, time)
        end_aware_dt = _parse_and_localize_datetime(date, end_time) if end_time else None
        
        # Validate end time is after start time
        if end_aware_dt and end_aware_dt <= aware_dt:
            return None, {"errors": "End time must be after start time."}
        
        # STEP 2: Time validation - Skip for VP/DIRECTOR/UESO, only check visible meetings for others
        # VP/DIRECTOR/UESO can schedule freely (they see all meetings anyway)
        user_role = getattr(user, 'role', None)
        if user_role not in ['VP', 'DIRECTOR', 'UESO']:
            # For PROGRAM_HEAD/DEAN/COORDINATOR/FACULTY/IMPLEMENTER
            # Only check meetings they can see (meetings where they are participants)
            overlapping_meetings = MeetingEvent.objects.filter(
                datetime__date=aware_dt.date(),
                participants=user  # Only check visible meetings (role-filtered)
            ).exclude(
                id=event.id  # Exclude the current event being edited
            ).exclude(
                end_datetime__isnull=True  # Only check meetings with end_datetime
            ).exclude(
                # Exclude meetings that don't overlap
                models.Q(datetime__gte=end_aware_dt) |  # Existing meeting starts after new meeting ends
                models.Q(end_datetime__lte=aware_dt)   # Existing meeting ends before new meeting starts
            )
            
            if overlapping_meetings.exists():
                conflict = overlapping_meetings.first()
                conflict_time = format_time_12hour(conflict.datetime)
                conflict_end = format_time_12hour(conflict.end_datetime) if conflict.end_datetime else 'N/A'
                return None, {"errors": f"Time conflict! \"{conflict.title}\" is already scheduled from {conflict_time} to {conflict_end} on this date."}
        
        # Check for participant conflicts (exclude current event)
        if participants:
            participant_ids = [str(p) for p in participants]
            
            # Find meetings on the same date that overlap in time and have common participants
            conflicting_meetings = MeetingEvent.objects.filter(
                datetime__date=aware_dt.date(),
                participants__id__in=participant_ids
            ).exclude(
                id=event.id  # Exclude the current event being edited
            ).exclude(
                end_datetime__isnull=True
            ).exclude(
                models.Q(datetime__gte=end_aware_dt) |
                models.Q(end_datetime__lte=aware_dt)
            ).distinct()
            
            if conflicting_meetings.exists():
                conflict = conflicting_meetings.first()
                conflict_time = format_time_12hour(conflict.datetime)
                conflict_end = format_time_12hour(conflict.end_datetime) if conflict.end_datetime else 'N/A'
                
                # Find which participants are conflicting by checking if they're in the conflict meeting's participants
                conflict_participant_ids = set(str(p.id) for p in conflict.participants.all())
                conflicting_ids = set(participant_ids).intersection(conflict_participant_ids)
                
                if conflicting_ids:
                    # Get the actual User objects for the conflicting participants
                    conflict_participants = User.objects.filter(id__in=conflicting_ids)
                    participant_names = [p.get_full_name() or p.username for p in conflict_participants]
                    if len(participant_names) == 1:
                        return None, {"errors": f"{participant_names[0]} is already scheduled in \"{conflict.title}\" from {conflict_time} to {conflict_end} on this date."}
                    else:
                        names_str = ", ".join(participant_names[:-1]) + f" and {participant_names[-1]}"
                        return None, {"errors": f"{names_str} are already scheduled in \"{conflict.title}\" from {conflict_time} to {conflict_end} on this date."}
        
        event.title = title
        event.description = description
        event.datetime = aware_dt
        event.end_datetime = end_aware_dt
        event.location = location
        event.updated_by = user
        event.notes = notes
        
        # Handle file attachment
        if notes_attachment:
            event.notes_attachment = notes_attachment
        elif data.get("remove_attachment"):  # Allow explicit removal
            event.notes_attachment = None
            
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
    user_role = getattr(user, 'role', None)
    if not (user == event.created_by or user_role in allowed_roles):
        return None, {"errors": "Permission denied."}
        
    try:
        event.delete()
        return True, None
    except Exception as e:
        return False, {"errors": str(e)}