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
    
    # Check if Google user needs role selection or profile completion
    # Show banner/notification but don't force redirect
    from system.users.views import is_google_profile_incomplete, is_google_account
    from system.users.models import User
    
    needs_role_selection = False
    needs_profile_completion = False
    
    if request.user.is_authenticated:
        # Check if needs role selection (non-PSU email with default CLIENT role)
        if (is_google_account(request.user) and 
            request.user.role == User.Role.CLIENT and 
            not request.user.email.lower().endswith('@psu.palawan.edu.ph')):
            # Check if they still have placeholder data
            if request.user.given_name in ['Google', ''] or request.user.last_name in ['User', '']:
                needs_role_selection = True
        
        # Check if profile is incomplete
        if is_google_profile_incomplete(request.user):
            needs_profile_completion = True
    
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
    events_json = '[]'
    
    # Notification counts for popup
    notifications = {}
    
    if request.user.is_authenticated and getattr(request.user, 'role', None) in FACULTY_ROLES:
        from internal.submissions.models import Submission
        from shared.event_calendar.models import MeetingEvent
        from shared.projects.models import ProjectUpdate
        from django.utils import timezone
        from datetime import timedelta
        
        faculty_projects = Project.objects.filter(
            models.Q(project_leader=request.user) | models.Q(providers=request.user)
        ).distinct().order_by('-updated_at')
        
        # Notification counts for faculty/implementer
        notifications['pending_submissions'] = Submission.objects.filter(
            project__in=faculty_projects,
            status='PENDING'
        ).count()
        notifications['revision_submissions'] = Submission.objects.filter(
            project__in=faculty_projects,
            status='REVISION_REQUESTED'
        ).count()
        notifications['rejected_submissions'] = Submission.objects.filter(
            project__in=faculty_projects,
            status='REJECTED'
        ).count()
        # Overdue submissions
        now = timezone.now()
        overdue_count = 0
        for submission in Submission.objects.filter(project__in=faculty_projects, status__in=['PENDING', 'REVISION_REQUESTED']):
            if submission.deadline and submission.deadline < now:
                overdue_count += 1
        notifications['overdue_submissions'] = overdue_count
        
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
    

    # Always provide all variables used in the template, even if empty/default
    if request.user.is_authenticated:
        context = {'is_user': True, 'user_role': getattr(request.user, 'role', None)}
    else:
        context = {'is_user': False, 'user_role': None}

    # Ensure all variables are present for the template
    latest_announcements = latest_announcements if 'latest_announcements' in locals() else []
    public_projects = public_projects if 'public_projects' in locals() else []
    public__project_image = public__project_image if 'public__project_image' in locals() else []
    faculty_projects = faculty_projects if 'faculty_projects' in locals() else []
    faculty_projects_image = faculty_projects_image if 'faculty_projects_image' in locals() else []
    pending_submissions_count = pending_submissions_count if 'pending_submissions_count' in locals() else 0
    ongoing_projects_count = ongoing_projects_count if 'ongoing_projects_count' in locals() else 0
    upcoming_meetings_count = upcoming_meetings_count if 'upcoming_meetings_count' in locals() else 0
    my_alerts = my_alerts if 'my_alerts' in locals() else []
    events_json = events_json if 'events_json' in locals() else '[]'
    notifications = notifications if 'notifications' in locals() else {}
    # Ensure all notification keys are present
    for key in ['pending_submissions', 'revision_submissions', 'rejected_submissions', 'overdue_submissions']:
        if key not in notifications:
            notifications[key] = 0
    show_notifications = show_notifications if 'show_notifications' in locals() else False

    from django.contrib.messages import get_messages
    storage = get_messages(request)
    
    # Add profile completion flags to context
    context['needs_role_selection'] = needs_role_selection if 'needs_role_selection' in locals() else False
    context['needs_profile_completion'] = needs_profile_completion if 'needs_profile_completion' in locals() else False
    show_notifications = any(str(msg) == "SHOW_REMINDERS" for msg in storage)
    
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
        'events_json': events_json,
        'notifications': notifications,
        'show_notifications': show_notifications,
        'needs_role_selection': needs_role_selection if 'needs_role_selection' in locals() else False,
        'needs_profile_completion': needs_profile_completion if 'needs_profile_completion' in locals() else False,
    }

    return render(request, 'home/home.html', render_context)