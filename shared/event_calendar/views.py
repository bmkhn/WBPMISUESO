from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from system.users.models import User
from django.shortcuts import render, get_object_or_404
from .models import MeetingEvent
from system.users.decorators import role_required
from shared.projects.models import ProjectEvent, Project
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from . import services


def get_templates(request):
    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"
    return base_template


@role_required(allowed_roles=["DIRECTOR", "VP", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD", "FACULTY", "IMPLEMENTER"], require_confirmed=True)
def calendar_view(request):
    base_template = get_templates(request)
    # Optimize users query - only need id, name, college for dropdown
    users = User.objects.exclude(role='CLIENT').select_related('college').only('id', 'given_name', 'last_name', 'college')
    initial_date = request.GET.get('date', None)
    events_by_date = services.get_events_by_date(request.user, for_main_calendar_view=True)
    events_json = json.dumps(events_by_date)
    
    context = {
        'users': users,
        'events_json': events_json,
        'base_template': base_template,
    }
    
    if initial_date:
        context['initial_date'] = initial_date

    return render(request, 'event_calendar/calendar.html', context)



@csrf_exempt
@role_required(allowed_roles=["DIRECTOR", "VP", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD", "FACULTY", "IMPLEMENTER"], require_confirmed=True)
@require_http_methods(["GET", "POST"])
def meeting_event_list(request):
    if request.method == "GET":
        events_by_date = services.get_events_by_date(request.user, for_main_calendar_view=False)
        return JsonResponse(events_by_date)
        
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            meeting, errors = services.create_meeting_event(data, request.user)
            if errors:
                return JsonResponse({"status": "error", "errors": errors.get("errors")}, status=400)
            return JsonResponse({"status": "success", "event_id": meeting.id}, status=201) 
        except Exception as e:
            return JsonResponse({"status": "error", "errors": str(e)}, status=500)

@csrf_exempt
@role_required(allowed_roles=["DIRECTOR", "VP", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD", "FACULTY", "IMPLEMENTER"], require_confirmed=True)
@require_http_methods(["PUT", "DELETE"]) 
def meeting_event_detail(request, event_id):
    event = get_object_or_404(MeetingEvent, id=event_id)
    
    if request.method == "PUT":
        if event.created_by != request.user:
            return JsonResponse({"status": "error", "errors": "Permission denied. Only the event creator can edit this meeting."}, status=403)
            
        try:
            data = json.loads(request.body)
            event, errors = services.update_meeting_event(event, data, request.user)
            if errors:
                status_code = 403 if errors.get("errors") == "Permission denied." else 400
                return JsonResponse({"status": "error", "errors": errors.get("errors")}, status=status_code)
            return JsonResponse({"status": "success", "event_id": event.id})
        except Exception as e:
            return JsonResponse({"status": "error", "errors": str(e)}, status=500)
            
    elif request.method == "DELETE":
        if event.created_by != request.user:
            return JsonResponse({"status": "error", "errors": "Permission denied. Only the event creator can delete this meeting."}, status=403)
            
        try:
            success, errors = services.delete_meeting_event(event, request.user)
            if errors:
                status_code = 403 if errors.get("errors") == "Permission denied." else 400
                return JsonResponse({"status": "error", "errors": errors.get("errors")}, status=status_code)
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "errors": str(e)}, status=500)