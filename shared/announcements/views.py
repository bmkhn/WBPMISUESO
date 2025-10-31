from django.http import HttpResponseRedirect
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse
from shared.announcements.forms import AnnouncementForm
from system.users.decorators import role_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Announcement
from django.db.models import Q, Case, When, DateTimeField
from urllib.parse import urlencode
import pytz


# Role-Based Dispatch View
def announcement_dispatch_view(request):
    user = request.user
    if not user.is_authenticated:
        return user_announcement_view(request)
    admin_roles = {"VP", "DIRECTOR", "UESO"}
    superuser_roles = {"PROGRAM_HEAD", "DEAN", "COORDINATOR"}
    role = getattr(user, 'role', None)
    if role in admin_roles:
        return announcement_admin_view(request)
    elif role in superuser_roles:
        return announcement_superuser_view(request)
    else:
        return user_announcement_view(request)


# Announcement Details Dispatch View
def announcement_details_dispatch_view(request, id):
    user = request.user
    announcement = get_object_or_404(Announcement, id=id)
    if not user.is_authenticated:
        return render(request, 'announcements/user_announcement_details.html', {'announcement': announcement})
    admin_roles = {"VP", "DIRECTOR", "UESO"}
    superuser_roles = {"PROGRAM_HEAD", "DEAN", "COORDINATOR"}
    role = getattr(user, 'role', None)
    if role in admin_roles:
        return render(request, 'announcements/admin_announcement_details.html', {'announcement': announcement})
    elif role in superuser_roles:
        return render(request, 'announcements/superuser_announcement_details.html', {'announcement': announcement})
    else:
        return render(request, 'announcements/user_announcement_details.html', {'announcement': announcement})


# User Announcement View
def user_announcement_view(request):
    search_query = request.GET.get('search', '').strip()
    sort_by = request.GET.get('sort')
    sort_order = request.GET.get('order')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if not sort_by:
        sort_by = 'date'
    if not sort_order:
        sort_order = 'desc'

    announcements_qs = Announcement.objects.filter(published_at__isnull=False, archived=False)

    if search_query:
        announcements_qs = announcements_qs.filter(
            Q(title__icontains=search_query) |
            Q(body__icontains=search_query)
        )

    if sort_by == 'date':
        if sort_order == 'desc':
            announcements_qs = announcements_qs.order_by('-published_at')
        else:
            announcements_qs = announcements_qs.order_by('published_at')
    elif sort_by == 'title':
        announcements_qs = announcements_qs.order_by(f'{"-" if sort_order=="desc" else ""}title')
    else:
        announcements_qs = announcements_qs.order_by('-published_at')

    if date_from:
        announcements_qs = announcements_qs.filter(published_at__date__gte=date_from)
    if date_to:
        announcements_qs = announcements_qs.filter(published_at__date__lte=date_to)

    paginator = Paginator(announcements_qs, 3)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)


    query_params = {}
    if search_query:
        query_params['search'] = search_query
    if sort_by and sort_by != 'date':
        query_params['sort'] = sort_by
    if sort_order and sort_order != 'desc':
        query_params['order'] = sort_order
    if date_from and date_from.strip():
        query_params['date_from'] = date_from
    if date_to and date_to.strip():
        query_params['date_to'] = date_to
    querystring = urlencode(query_params)

    current = page_obj.number
    total = paginator.num_pages
    if total <= 5:
        page_range = range(1, total + 1)
    elif current <= 3:
        page_range = range(1, 6)
    elif current >= total - 2:
        page_range = range(total - 4, total + 1)
    else:
        page_range = range(current - 2, current + 3)

    return render(request, 'announcements/user_announcement.html', {
        'announcements': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'search_query': search_query,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'date_from': date_from,
        'date_to': date_to,
        'querystring': querystring,
        "page_range": page_range,
    })


# SuperUser Announcement View
@role_required(allowed_roles=["PROGRAM_HEAD", "DEAN", "COORDINATOR"], require_confirmed=True)
def announcement_superuser_view(request):
    search_query = request.GET.get('search', '').strip()
    sort_by = request.GET.get('sort')
    sort_order = request.GET.get('order')

    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if not sort_by:
        sort_by = 'date'
    if not sort_order:
        sort_order = 'desc'

    announcements_qs = Announcement.objects.filter(published_at__isnull=False, archived=False)

    if search_query:
        announcements_qs = announcements_qs.filter(
            Q(title__icontains=search_query) |
            Q(body__icontains=search_query)
        )

    if sort_by == 'date':
        if sort_order == 'desc':
            announcements_qs = announcements_qs.order_by('-published_at')
        else:
            announcements_qs = announcements_qs.order_by('published_at')
    elif sort_by == 'title':
        announcements_qs = announcements_qs.order_by(f'{"-" if sort_order=="desc" else ""}title')
    else:
        announcements_qs = announcements_qs.order_by('-published_at')

    if date_from:
        announcements_qs = announcements_qs.filter(published_at__date__gte=date_from)
    if date_to:
        announcements_qs = announcements_qs.filter(published_at__date__lte=date_to)



    paginator = Paginator(announcements_qs, 3)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)


    query_params = {}
    if search_query:
        query_params['search'] = search_query
    if sort_by and sort_by != 'date':
        query_params['sort'] = sort_by
    if sort_order and sort_order != 'desc':
        query_params['order'] = sort_order
    if date_from and date_from.strip():
        query_params['date_from'] = date_from
    if date_to and date_to.strip():
        query_params['date_to'] = date_to
    querystring = urlencode(query_params)

    current = page_obj.number
    total = paginator.num_pages
    if total <= 5:
        page_range = range(1, total + 1)
    elif current <= 3:
        page_range = range(1, 6)
    elif current >= total - 2:
        page_range = range(total - 4, total + 1)
    else:
        page_range = range(current - 2, current + 3)

    return render(request, 'announcements/superuser_announcement.html', {
        'announcements': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'search_query': search_query,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'date_from': date_from,
        'date_to': date_to,
        'querystring': querystring,
        "page_range": page_range,
    })


# Admin Announcement View
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def announcement_admin_view(request):
    search_query = request.GET.get('search', '').strip()
    sort_by = request.GET.get('sort')
    sort_order = request.GET.get('order')
    if not sort_by:
        sort_by = 'date'
    if not sort_order:
        sort_order = 'desc'
    filter_status = request.GET.get('status', '')
    filter_author = request.GET.get('author', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    filter_edited = request.GET.get('edited', '')

    announcements_qs = Announcement.objects.all()

    if search_query:
        announcements_qs = announcements_qs.filter(
            Q(title__icontains=search_query) |
            Q(body__icontains=search_query)
        )

    if filter_status:
        if filter_status == 'published':
            announcements_qs = announcements_qs.filter(published_at__isnull=False)
        elif filter_status == 'scheduled':
            announcements_qs = announcements_qs.filter(is_scheduled=True)
        elif filter_status == 'archived':
            announcements_qs = announcements_qs.filter(archived=True)
        elif filter_status == 'unarchived':
            announcements_qs = announcements_qs.filter(archived=False)

    if filter_author:
        announcements_qs = announcements_qs.filter(published_by__id=filter_author)

    # Filter by published_at or scheduled_at date range
    if date_from:
        announcements_qs = announcements_qs.filter(
            Q(published_at__date__gte=date_from) | Q(scheduled_at__date__gte=date_from)
        )
    if date_to:
        announcements_qs = announcements_qs.filter(
            Q(published_at__date__lte=date_to) | Q(scheduled_at__date__lte=date_to)
        )

    if filter_edited == 'true':
        announcements_qs = announcements_qs.filter(edited_at__isnull=False)
    elif filter_edited == 'false':
        announcements_qs = announcements_qs.filter(edited_at__isnull=True)

    if sort_by == 'date':
        if sort_order == 'desc':
            announcements_qs = announcements_qs.annotate(
                sort_date=Case(
                    When(published_at__isnull=False, then='published_at'),
                    When(published_at__isnull=True, then='scheduled_at'),
                    default='scheduled_at',
                    output_field=DateTimeField()
                )
            ).order_by('-sort_date')
        else:
            announcements_qs = announcements_qs.annotate(
                sort_date=Case(
                    When(published_at__isnull=False, then='published_at'),
                    When(published_at__isnull=True, then='scheduled_at'),
                    default='scheduled_at',
                    output_field=DateTimeField()
                )
            ).order_by('sort_date')
    else:
        sort_map = {
            'title': 'title',
            'status': 'is_scheduled',
            'edited': 'edited_at',
        }
        sort_field = sort_map.get(sort_by, 'published_at')
        if sort_order == 'desc':
            sort_field = '-' + sort_field
        announcements_qs = announcements_qs.order_by(sort_field)

    paginator = Paginator(announcements_qs, 6)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    from system.users.models import User
    authors = User.objects.filter(id__in=Announcement.objects.values_list('published_by', flat=True))
    from urllib.parse import urlencode
    query_params = {}
    if search_query:
        query_params['search'] = search_query
    if sort_by and sort_by != 'date' and sort_by.strip():
        query_params['sort'] = sort_by
    if sort_order and sort_order != 'desc' and sort_order.strip():
        query_params['order'] = sort_order
    if filter_status and filter_status.strip():
        query_params['status'] = filter_status
    if filter_author and filter_author.strip():
        query_params['author'] = filter_author
    if date_from and date_from.strip():
        query_params['date_from'] = date_from
    if date_to and date_to.strip():
        query_params['date_to'] = date_to
    if filter_edited and filter_edited.strip():
        query_params['edited'] = filter_edited
    querystring = urlencode(query_params)

    current = page_obj.number
    total = paginator.num_pages
    if total <= 5:
        page_range = range(1, total + 1)
    elif current <= 3:
        page_range = range(1, 6)
    elif current >= total - 2:
        page_range = range(total - 4, total + 1)
    else:
        page_range = range(current - 2, current + 3)
        
    return render(request, 'announcements/admin_announcement.html', {
        'announcements': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'search_query': search_query,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'filter_status': filter_status,
        'filter_author': filter_author,
        'date_from': date_from,
        'date_to': date_to,
        'filter_edited': filter_edited,
        'authors': authors,
        'querystring': querystring,
        "page_range": page_range,
    })


# Add Announcement View
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def add_announcement_view(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            scheduled_at = form.cleaned_data.get('scheduled_at')
            now = timezone.now()
            is_immediate = False
            
            if scheduled_at and scheduled_at > now:             # If scheduled_at is in the future
                announcement.is_scheduled = True
                announcement.published_at = None
                announcement.scheduled_at = scheduled_at
                announcement.scheduled_by = request.user
            else:                                               # If scheduled_at is empty, publish now
                announcement.is_scheduled = False
                announcement.published_at = now
                announcement.scheduled_at = None
                is_immediate = True
                
            announcement.published_by = request.user
            announcement.save()
            
            # Redirect with toast parameters
            from urllib.parse import quote
            title = quote(announcement.title)
            return redirect(f"{reverse('announcement_dispatcher')}?success=true&action=added&title={title}")
    else:
        form = AnnouncementForm()
    return render(request, 'announcements/add_announcement.html', {"form": form})


# Edit Announcement View
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def edit_announcement_view(request, id):

    announcement = get_object_or_404(Announcement, id=id)
    was_scheduled = announcement.is_scheduled
    
    if request.method == 'POST':
        # Check if user wants to remove the cover photo
        if request.POST.get('remove_cover_photo') == 'true':
            if announcement.cover_photo:
                announcement.cover_photo.delete(save=False)
                announcement.cover_photo = None
        
        form = AnnouncementForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            edited = form.save(commit=False)
            scheduled_at = form.cleaned_data.get('scheduled_at')
            now = timezone.now()
            edited.edited_by = request.user
            edited.edited_at = now
            send_email = False
            
            if not scheduled_at:                                # If scheduled_at is empty, not scheduled
                # If this was previously scheduled and now being published immediately
                if was_scheduled and not edited.published_at:
                    send_email = True
                edited.published_at = now
                edited.is_scheduled = False
                edited.scheduled_at = None
                edited.scheduled_by = None
            else:                                               # If scheduled_at is provided, it is scheduled
                edited.is_scheduled = True
                edited.scheduled_at = scheduled_at
                edited.scheduled_by = request.user

            edited.save()
            
            # Redirect with toast parameters
            from urllib.parse import quote
            title = quote(edited.title)
            return redirect(f"{reverse('announcement_dispatcher')}?success=true&action=edited&title={title}")
    else:
        form = AnnouncementForm(instance=announcement)
    return render(request, 'announcements/edit_announcement.html', {"form": form, "announcement": announcement})


# Delete Announcement View
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"])
def delete_announcement_view(request, id):
    from .models import Announcement
    announcement = get_object_or_404(Announcement, id=id)
    title = announcement.title
    announcement.delete()
    
    # Redirect with toast parameters
    from urllib.parse import quote
    title_encoded = quote(title)
    return redirect(f"{reverse('announcement_dispatcher')}?success=true&action=deleted&title={title_encoded}")

# Archive Announcement View
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"])
def archive_announcement_view(request, id):
    announcement = get_object_or_404(Announcement, id=id)
    if request.method == 'POST' or request.method == 'GET':
        title = announcement.title
        announcement.archived = True
        announcement.save()
        
        # Redirect with toast parameters
        from urllib.parse import quote
        title_encoded = quote(title)
        return redirect(f"{reverse('announcement_dispatcher')}?success=true&action=archived&title={title_encoded}")
    return redirect('announcement_dispatcher')


# Unarchive Announcement View
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"])
def unarchive_announcement_view(request, id):
    announcement = get_object_or_404(Announcement, id=id)
    if request.method == 'POST' or request.method == 'GET':
        title = announcement.title
        announcement.archived = False
        announcement.save()
        
        # Redirect with toast parameters
        from urllib.parse import quote
        title_encoded = quote(title)
        return redirect(f"{reverse('announcement_dispatcher')}?success=true&action=unarchived&title={title_encoded}")
    return redirect('announcement_dispatcher')