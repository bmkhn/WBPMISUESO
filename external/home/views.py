from django.shortcuts import redirect, render
from django.db import models
from shared.announcements.models import Announcement
from shared.projects.models import Project 
import json
 
from shared.event_calendar import services as calendar_services
from django.http import JsonResponse
from django.db.models import Count
from collections import OrderedDict

def get_role_constants():
    PUBLIC_ROLES = [None, 'CLIENT']
    FACULTY_ROLES = ['FACULTY', 'IMPLEMENTER']
    return PUBLIC_ROLES, FACULTY_ROLES

def home_view(request):
    PUBLIC_ROLES, FACULTY_ROLES = get_role_constants()
    if request.user.is_authenticated and not getattr(request.user, 'is_confirmed', True):
        return redirect('not_confirmed')
    
    def get_project_card_data(project_qs):
        projects_data = []
        for project in project_qs:
            # Use the model method to get display image
            image_url = project.get_display_image_url()
            agenda = project.agenda.name if project.agenda else ''
            projects_data.append({
                'id': project.id,
                'title': project.title,
                'image_url': image_url,
                'agenda': agenda,
            })
        return projects_data

    public_projects = Project.objects.filter(status='COMPLETED').order_by('-updated_at')
    public__project_image = get_project_card_data(public_projects[:2])

    # Faculty-specific data
    faculty_projects = []
    faculty_projects_image = []
    pending_submissions_count = 0
    ongoing_projects_count = 0
    upcoming_meetings_count = 0
    my_alerts = []
    
    if request.user.is_authenticated and getattr(request.user, 'role', None) in FACULTY_ROLES:
        from internal.submissions.models import Submission
        from shared.event_calendar.models import MeetingEvent
        from shared.projects.models import ProjectUpdate
        from django.utils import timezone
        from datetime import timedelta
        
        faculty_projects = Project.objects.filter(
            models.Q(project_leader=request.user) | models.Q(providers=request.user)
        ).distinct().order_by('-updated_at')
        
        faculty_projects_image = get_project_card_data(faculty_projects.filter(status='COMPLETED')[:3])
        
        # Get stats
        pending_submissions_count = Submission.objects.filter(
            project__in=faculty_projects,
            status__in=['PENDING', 'REVISION_REQUESTED']
        ).count()
        
        ongoing_projects_count = faculty_projects.filter(status='IN_PROGRESS').count()
        
        # Get alerts
        my_alerts = ProjectUpdate.objects.filter(
            user=request.user,
            viewed=False
        ).select_related('project', 'submission').order_by('-updated_at')[:5]
         
        events_by_date = calendar_services.get_events_by_date(request.user, for_main_calendar_view=True)
        events_json = json.dumps(events_by_date)

    latest_announcements = Announcement.objects.filter(published_at__isnull=False, archived=False).order_by('-published_at')[:2]
    if request.user.is_authenticated:
        context = {'is_user': True, 'user_role': getattr(request.user, 'role', None)}
    else:
        context = {'is_user': False}
    render_context = {
        'context': context,
        'latest_announcements': latest_announcements,
        'PUBLIC_ROLES': PUBLIC_ROLES,
        'FACULTY_ROLES': FACULTY_ROLES,
        'public_projects': public_projects,
        'public__project_image': public__project_image,
        'faculty_projects': faculty_projects,
        'faculty_projects_image': faculty_projects_image,
        'pending_submissions_count': pending_submissions_count,
        'ongoing_projects_count': ongoing_projects_count,
        'upcoming_meetings_count': upcoming_meetings_count,
        'my_alerts': my_alerts,
    }

    if request.user.is_authenticated:
        render_context['events_json'] = events_json

    return render(request, 'home/home.html', render_context)