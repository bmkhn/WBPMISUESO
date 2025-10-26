from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from system.users.models import User
from django.shortcuts import render
from .models import MeetingEvent
from system.users.decorators import role_required
from shared.projects.models import ProjectEvent, Project


@role_required(allowed_roles=["DIRECTOR", "VP", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD", "FACULTY", "IMPLEMENTER"], require_confirmed=True)
def calendar_view(request):
    from system.users.models import User
    current_user = request.user
    users = User.objects.exclude(role='CLIENT')
    from .models import MeetingEvent
    # Gather all events, group by date
    events_qs = MeetingEvent.objects.all()
    project_events_qs = ProjectEvent.objects.select_related('project').filter(placeholder=False)
    events_by_date = {}
    from django.utils import timezone
    # MeetingEvents
    for event in events_qs:
        local_dt = timezone.localtime(event.datetime)
        date_str = local_dt.strftime('%Y-%m-%d')
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append({
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
        })
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
    import json
    events_json = json.dumps(events_by_date)
    if current_user.role == 'FACULTY' or current_user.role == 'IMPLEMENTER':
        return render(request, 'event_calendar/calendar.html', {
            'users': users,
            'events_json': events_json,
        })
    elif current_user.role in ['VP', 'DIRECTOR', 'UESO', 'COORDINATOR', 'DEAN', 'PROGRAM_HEAD']:
        return render(request, 'event_calendar/calendar_admin.html', {
            'users': users,
            'events_json': events_json,
        })  


@role_required(allowed_roles=["DIRECTOR", "VP", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD", "FACULTY", "IMPLEMENTER"], require_confirmed=True)
def add_event(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            title = data.get("title", "").strip()
            description = data.get("description", "").strip()
            date = data.get("date")
            time = data.get("time")
            location = data.get("location", "").strip()
            participants = data.get("participants", [])
            notes = data.get("notes", "")
            if not (title and description and date and time and location):
                return JsonResponse({"status": "error", "errors": "Missing required fields."})
            from datetime import datetime
            from django.utils import timezone
            import pytz
            dt_str = f"{date} {time}"
            naive_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            local_tz = pytz.timezone("Asia/Manila")
            aware_dt = local_tz.localize(naive_dt)
            meeting = MeetingEvent.objects.create(
                title=title,
                description=description,
                datetime=aware_dt,
                location=location,
                created_by=request.user,
                updated_by=request.user,
                notes=notes
            )
            if participants:
                users = User.objects.filter(id__in=participants)
                meeting.participants.set(users)
            meeting.save()
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "errors": str(e)})
    return JsonResponse({"status": "error", "errors": "Invalid request method."})


from django.views.decorators.http import require_GET

@role_required(allowed_roles=["DIRECTOR", "VP", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD", "FACULTY", "IMPLEMENTER"], require_confirmed=True)
@require_GET
def events_json(request):
    from .models import MeetingEvent
    from shared.projects.models import ProjectEvent, Project
    from django.db import models
    user = request.user
    events_qs = MeetingEvent.objects.none()
    project_events_qs = ProjectEvent.objects.select_related('project').none()
    from system.users.models import User
    from shared.projects.models import Project
    if user.role in ['UESO', 'VP', 'DIRECTOR']:
        print("User is UESO/VP/DIRECTOR, fetching all events")
        events_qs = MeetingEvent.objects.all()
        project_events_qs = ProjectEvent.objects.select_related('project').filter(placeholder=False)
    elif user.role in ['PROGRAM_HEAD', 'DEAN', 'COORDINATOR']:
        print("User is PROGRAM_HEAD/DEAN/COORDINATOR, fetching college events")
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
    from django.utils import timezone
    for event in events_qs:
        local_dt = timezone.localtime(event.datetime)
        date_str = local_dt.strftime('%Y-%m-%d')
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append({
            'id': event.id,
            'type': 'meeting',
            'title': event.title,
            'description': event.description,
            'date': date_str,
            'time': local_dt.strftime('%H:%M'),
            'location': event.location,
            'notes': event.notes,
            'status': event.status,
            'participant_names': [u.get_full_name() or u.username for u in event.participants.all()],
        })
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
    return JsonResponse(events_by_date)


from django.views.decorators.csrf import csrf_exempt
@role_required(allowed_roles=["DIRECTOR", "VP", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD", "FACULTY", "IMPLEMENTER"], require_confirmed=True)
@csrf_exempt
def edit_event(request):
    if request.method == "POST":
        try:
            print("DEBUG Content-Type:", request.content_type)
            if request.content_type.startswith("application/json"):
                data = json.loads(request.body)
                event_id = data.get("event_id")
                title = data.get("title", "").strip()
                description = data.get("description", "").strip()
                date = data.get("date")
                time = data.get("time")
                location = data.get("location", "").strip()
                participants = data.get("participants", [])
                notes = data.get("notes", "")
            else:
                event_id = request.POST.get("event_id")
                title = request.POST.get("title", "").strip()
                description = request.POST.get("description", "").strip()
                date = request.POST.get("date")
                time = request.POST.get("time")
                location = request.POST.get("location", "").strip()
                participants = request.POST.getlist("participants[]")
                notes = request.POST.get("notes", "")
            if not (event_id and title and description and date and time and location):
                return JsonResponse({"status": "error", "errors": "Missing required fields."})
            from datetime import datetime
            from django.utils import timezone
            import pytz
            dt_str = f"{date} {time}"
            naive_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            local_tz = pytz.timezone("Asia/Manila")
            aware_dt = local_tz.localize(naive_dt)
            event = MeetingEvent.objects.filter(id=event_id).first()
            if not event:
                return JsonResponse({"status": "error", "errors": "Event not found."})
            # Permission: Only creator or DIRECTOR/UESO/VP can edit
            allowed_roles = ["DIRECTOR", "UESO", "VP"]
            if not (request.user == event.created_by or request.user.role in allowed_roles):
                return JsonResponse({"status": "error", "errors": "Permission denied."})
            event.title = title
            event.description = description
            event.datetime = aware_dt
            event.location = location
            event.updated_by = request.user
            event.notes = notes
            event.save()
            if participants:
                users = User.objects.filter(id__in=participants)
                event.participants.set(users)
            else:
                event.participants.clear()
            # Redirect for regular form POST, JSON for AJAX
            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
            if request.content_type.startswith("application/json") or is_ajax:
                return JsonResponse({"status": "success"})
            else:
                from django.http import HttpResponseRedirect
                from django.urls import reverse
                return HttpResponseRedirect(reverse('calendar'))
        except Exception as e:
            return JsonResponse({"status": "error", "errors": str(e)})
    return JsonResponse({"status": "error", "errors": "Invalid request method."})


# Delete Event View
@role_required(allowed_roles=["DIRECTOR", "VP", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD", "FACULTY", "IMPLEMENTER"], require_confirmed=True)
@csrf_exempt
def delete_event(request, event_id):
    if request.method == "POST":
        try:
            event = MeetingEvent.objects.filter(id=event_id).first()
            if not event:
                return JsonResponse({"status": "error", "errors": "Event not found."})
            allowed_roles = ["DIRECTOR", "UESO", "VP"]
            if not (request.user == event.created_by or request.user.role in allowed_roles):
                return JsonResponse({"status": "error", "errors": "Permission denied."})
            event.delete()
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "errors": str(e)})
    return JsonResponse({"status": "error", "errors": "Invalid request method."})