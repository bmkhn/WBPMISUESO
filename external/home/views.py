from django.shortcuts import render
from shared.announcements.models import Announcement

def get_role_constants():
    PUBLIC_ROLES = [None, 'CLIENT']
    FACULTY_ROLES = ['FACULTY']
    return PUBLIC_ROLES, FACULTY_ROLES

def home_view(request):
    PUBLIC_ROLES, FACULTY_ROLES = get_role_constants()

    latest_announcements = Announcement.objects.filter(
        published_at__isnull=False,
        archived=False
    ).order_by('-published_at')[:2]
    if request.user.is_authenticated:
        context = {'is_user': True, 'user_role': getattr(request.user, 'role', None)}
    else:
        context = {'is_user': False}
    return render(request, 'home/home.html', {
        'context': context,
        'latest_announcements': latest_announcements,
        'PUBLIC_ROLES': PUBLIC_ROLES,
        'FACULTY_ROLES': FACULTY_ROLES
    }) 