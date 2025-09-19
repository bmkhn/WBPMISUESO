from django.shortcuts import render
from shared.announcements.models import Announcement

def home_view(request):
    latest_announcements = Announcement.objects.filter(published_at__isnull=False).order_by('-published_at')[:2]
    if request.user.is_authenticated:
        context = {'is_user': True, 'user_role': getattr(request.user, 'role', None)}
    else:
        context = {'is_user': False}
    return render(request, 'home/home.html', {
        'context': context,
        'latest_announcements': latest_announcements,
    }) 