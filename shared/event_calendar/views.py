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
            # Check if it's FormData (file upload) or JSON
            if request.content_type and 'multipart/form-data' in request.content_type:
                # FormData with file
                data = {
                    'title': request.POST.get('title', ''),
                    'description': request.POST.get('description', ''),
                    'date': request.POST.get('date', ''),
                    'time': request.POST.get('time', ''),
                    'location': request.POST.get('location', ''),
                    'notes': request.POST.get('notes', ''),
                    'participants': request.POST.getlist('participants[]', []),
                    'notes_attachment': request.FILES.get('notes_attachment')
                }
            else:
                # Check if there's any POST data (FormData without explicit content-type)
                if request.POST:
                    data = {
                        'title': request.POST.get('title', ''),
                        'description': request.POST.get('description', ''),
                        'date': request.POST.get('date', ''),
                        'time': request.POST.get('time', ''),
                        'location': request.POST.get('location', ''),
                        'notes': request.POST.get('notes', ''),
                        'participants': request.POST.getlist('participants[]', []),
                        'notes_attachment': request.FILES.get('notes_attachment')
                    }
                else:
                    # Regular JSON
                    data = json.loads(request.body)
                
            meeting, errors = services.create_meeting_event(data, request.user)
            if errors:
                return JsonResponse({"status": "error", "errors": errors.get("errors")}, status=400)
            
            return JsonResponse({"status": "success", "event_id": meeting.id}, status=201) 
        except Exception as e:
            import traceback
            traceback.print_exc()
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
            # Django doesn't populate request.POST and request.FILES for PUT requests
            # We need to manually parse the request body
            from django.http.multipartparser import MultiPartParser
            from django.http import QueryDict
            
            # Check if it's FormData (file upload) or JSON
            content_type = request.META.get('CONTENT_TYPE', '')
            
            if 'multipart/form-data' in content_type:
                # For PUT requests with multipart data, we need to manually parse
                # Use MultiPartParser directly
                parser = MultiPartParser(request.META, request, request.upload_handlers)
                post_data, files = parser.parse()
                
                data = {
                    'title': post_data.get('title', ''),
                    'description': post_data.get('description', ''),
                    'date': post_data.get('date', ''),
                    'time': post_data.get('time', ''),
                    'location': post_data.get('location', ''),
                    'notes': post_data.get('notes', ''),
                    'participants': post_data.getlist('participants[]', []),
                    'notes_attachment': files.get('notes_attachment'),
                    'remove_attachment': post_data.get('remove_attachment') == 'true'
                }
                
                # Debug logging
                print("=== PUT REQUEST DEBUG ===")
                print(f"Content-Type: {content_type}")
                print(f"POST data: {dict(post_data)}")
                print(f"FILES data: {dict(files)}")
                print(f"Parsed data: {data}")
                print("========================")
            else:
                # Regular JSON
                data = json.loads(request.body)
                
            event, errors = services.update_meeting_event(event, data, request.user)
            if errors:
                status_code = 403 if errors.get("errors") == "Permission denied." else 400
                return JsonResponse({"status": "error", "errors": errors.get("errors")}, status=status_code)
            return JsonResponse({"status": "success", "event_id": event.id})
        except Exception as e:
            import traceback
            traceback.print_exc()
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
        
# ... keep existing imports (if any)
from rest_framework import viewsets, permissions
from rest_framework.authentication import TokenAuthentication # Use Token auth for users
from django.db.models import Q

from .models import MeetingEvent
from .serializers import MeetingEventSerializer
from .permissions import IsEventOwner

class MeetingEventViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows calendar events to be viewed or edited.
    
    - Provides full CRUD (POST, GET, PUT, PATCH, DELETE).
    - Users can see all events they created OR are a participant in.
    - Users can ONLY edit/delete events they created.
    """
    serializer_class = MeetingEventSerializer
    
    # Use TokenAuthentication to identify which user is making the request
    authentication_classes = [TokenAuthentication] 
    
    # Users must be authenticated, and can only edit/delete their own events
    permission_classes = [permissions.IsAuthenticated, IsEventOwner]

    def get_queryset(self):
        """
        This view should return a list of all the events
        for the currently authenticated user.
        
        It returns events where the user is EITHER the creator
        OR one of the participants.
        """
        user = self.request.user
        if user.is_staff:
            # Admins can see all events
            return MeetingEvent.objects.all()
        
        # Regular users see events they created or are participating in
        return MeetingEvent.objects.filter(
            Q(created_by=user) | Q(participants=user)
        ).distinct()

    def perform_create(self, serializer):
        """
        Automatically set the created_by and updated_by user
        to the user making the request when a new event is created.
        """
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        """
        Automatically set the updated_by user when an event is edited.
        """
        serializer.save(updated_by=self.request.user)