from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from shared.announcements.forms import AnnouncementForm
from system.users.decorators import role_required
from django.shortcuts import get_object_or_404
from django.utils import timezone

@login_required
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"])
def announcement_admin_view(request):
    from .models import Announcement
    announcements = Announcement.objects.order_by('-published_at')
    return render(request, 'announcements/admin_announcement.html', {'announcements': announcements})


@login_required
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"])
def add_announcement_view(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            scheduled_at = form.cleaned_data.get('scheduled_at')
            if scheduled_at and scheduled_at > timezone.now():
                announcement.is_scheduled = True
            else:
                announcement.is_scheduled = False
            announcement.published_by = request.user
            announcement.save()
            return redirect('announcement_admin')
    else:
        form = AnnouncementForm()
    return render(request, 'announcements/add_announcement.html', {"form": form})


@login_required
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"])
def delete_announcement_view(request, id):
    from .models import Announcement
    announcement = get_object_or_404(Announcement, id=id)
    if request.method == 'POST':
        announcement.delete()
        return redirect('announcement_admin')
    return render(request, 'announcements/delete_confirm.html', {"announcement": announcement})


@login_required
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"])
def edit_announcement_view(request, id):
    from .models import Announcement
    announcement = get_object_or_404(Announcement, id=id)
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            edited = form.save(commit=False)
            edited.edited_by = request.user
            edited.edited_at = timezone.now()
            edited.save()
            return redirect('announcement_admin')
    else:
        form = AnnouncementForm(instance=announcement)
    return render(request, 'announcements/edit_announcement.html', {"form": form, "announcement": announcement})