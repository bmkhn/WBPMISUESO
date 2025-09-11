from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from shared.announcements.forms import AnnouncementForm
from system.users.decorators import role_required

@login_required
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"])
def add_announcement_view(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.published_by = request.user
            announcement.save()
            return redirect('announcement_admin')
    else:
        form = AnnouncementForm()
    return render(request, 'announcements/add_announcement.html', {"form": form})

@login_required
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"])
def announcement_admin_view(request):
    from .models import Announcement
    announcements = Announcement.objects.order_by('-published_at')
    return render(request, 'announcements/admin_announcement.html', {'announcements': announcements})