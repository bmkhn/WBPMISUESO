import json
from django.http import JsonResponse
from system.users.models import User
from django.shortcuts import render
from .models import MeetingEvent
from django.contrib.auth.decorators import login_required
from system.users.decorators import role_required


@login_required
@role_required(allowed_roles=["DIRECTOR", "VP", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD", "FACULTY", "IMPLEMENTER"])
def calendar_view(request):
    from system.users.models import User
    users = User.objects.exclude(role='CLIENT')
    from .models import MeetingEvent
    # Gather all events, group by date
    events_qs = MeetingEvent.objects.all()
    events_by_date = {}
    from django.utils import timezone
    for event in events_qs:
        local_dt = timezone.localtime(event.datetime)
        date_str = local_dt.strftime('%Y-%m-%d')
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'date': date_str,
            'time': local_dt.strftime('%H:%M'),
            'location': event.location,
            'notes': event.notes,
            'status': event.status,
        })
    import json
    events_json = json.dumps(events_by_date)
    return render(request, 'event_calendar/calendar.html', {'users': users, 'events_json': events_json})


@login_required
@role_required(allowed_roles=["DIRECTOR", "VP", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD", "FACULTY", "IMPLEMENTER"])
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

@login_required
@role_required(allowed_roles=["DIRECTOR", "VP", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD", "FACULTY", "IMPLEMENTER"])
@require_GET
def events_json(request):
    from .models import MeetingEvent
    events_qs = MeetingEvent.objects.all()
    events_by_date = {}
    from django.utils import timezone
    for event in events_qs:
        local_dt = timezone.localtime(event.datetime)
        date_str = local_dt.strftime('%Y-%m-%d')
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'date': date_str,
            'time': local_dt.strftime('%H:%M'),
            'location': event.location,
            'notes': event.notes,
            'status': event.status,
        })
    return JsonResponse(events_by_date)


from django.views.decorators.csrf import csrf_exempt
@login_required
@role_required(allowed_roles=["DIRECTOR", "VP", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD", "FACULTY", "IMPLEMENTER"])
@csrf_exempt
def edit_event(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            event_id = data.get("event_id")
            title = data.get("title", "").strip()
            description = data.get("description", "").strip()
            date = data.get("date")
            time = data.get("time")
            location = data.get("location", "").strip()
            participants = data.get("participants", [])
            notes = data.get("notes", "")
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
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "errors": str(e)})
    return JsonResponse({"status": "error", "errors": "Invalid request method."})