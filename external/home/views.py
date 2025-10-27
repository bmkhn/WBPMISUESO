from django.shortcuts import redirect, render
from django.db import models
from shared.announcements.models import Announcement
from shared.projects.models import Project

def get_role_constants():
    PUBLIC_ROLES = [None, 'CLIENT']
    FACULTY_ROLES = ['FACULTY']
    return PUBLIC_ROLES, FACULTY_ROLES

def home_view(request):
    PUBLIC_ROLES, FACULTY_ROLES = get_role_constants()
    if request.user.is_authenticated and not getattr(request.user, 'is_confirmed', True):
        return redirect('not_confirmed')
    
    def get_project_card_data(project_qs):
        projects_data = []
        for project in project_qs:
            # Get latest event with image
            event = project.events.filter(image__isnull=False).order_by('-datetime').first()
            image_url = event.image.url if event and event.image else None
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

    if request.user.is_authenticated and getattr(request.user, 'role', None) in FACULTY_ROLES:
        faculty_projects = Project.objects.filter(status='COMPLETED').filter(models.Q(project_leader=request.user) | models.Q(providers=request.user)).distinct().order_by('-updated_at')
        faculty_projects_image = get_project_card_data(faculty_projects[:2])
    else:
        faculty_projects = []
        faculty_projects_image = []

    latest_announcements = Announcement.objects.filter(published_at__isnull=False, archived=False).order_by('-published_at')[:2]
    if request.user.is_authenticated:
        context = {'is_user': True, 'user_role': getattr(request.user, 'role', None)}
    else:
        context = {'is_user': False}
    return render(request, 'home/home.html', {
        'context': context,
        'latest_announcements': latest_announcements,
        'PUBLIC_ROLES': PUBLIC_ROLES,
        'FACULTY_ROLES': FACULTY_ROLES,
        'public_projects': public_projects,
        'public__project_image': public__project_image,
        'faculty_projects': faculty_projects,
        'faculty_projects_image': faculty_projects_image
    })