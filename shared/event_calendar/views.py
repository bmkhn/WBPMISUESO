from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Event
from django.contrib.auth.decorators import login_required
from system.users.decorators import role_required

@login_required
@role_required(allowed_roles=["DIRECTOR", "VP", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD", "FACULTY"])
def calendar_view(request):
    return render(request, 'event_calendar/calendar.html') 

@login_required
@role_required(allowed_roles=["DIRECTOR", "VP", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD", "FACULTY"])
def get_events(request):
    year = int(request.GET.get('year'))
    month = int(request.GET.get('month'))

    events = Event.objects.filter(
        date__year=year,
        date__month=month
    ).values('title', 'date', 'location')

    return JsonResponse(list(events), safe=False)

@login_required
@role_required(allowed_roles=["DIRECTOR", "VP", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD", "FACULTY"])
@csrf_exempt
def add_event(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            event = Event.objects.create(
                title=data.get('title', ''),
                date=data.get('date', ''),
                location=data.get('location', ''),
                notes=data.get('notes', '')
            )
            return JsonResponse({'status': 'success', 'event_id': event.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})