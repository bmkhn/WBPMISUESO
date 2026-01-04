from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.urls import reverse
from .forms import DownloadableForm
from django.shortcuts import render, redirect
from system.users.decorators import role_required
from django.core.paginator import Paginator
from .models import Downloadable
import mimetypes
import os
from urllib.parse import urlencode
from django.views.decorators.http import require_POST


def downloadable_dispatcher(request):
    user = request.user
    if hasattr(user, 'role'):
        role = user.role
        if role in ["UESO", "DIRECTOR", "VP"]:
            return admin_downloadable(request)
        elif role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
            return superuser_downloadable(request)
        else:
            return user_downloadable(request)
    return user_downloadable(request)


def user_downloadable(request):
    user = request.user
    query_params = {}

    if user.is_authenticated:
        # Faculty/Client: see all published files except archived - optimize with select_related
        qs = Downloadable.objects.filter(status='published').select_related('uploaded_by')
    else:
        # Non-Users: only see files available for public
        qs = Downloadable.objects.filter(status='published', available_for_non_users=True).select_related('uploaded_by')
        query_params['public'] = 'true'

    # Search by
    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(file__icontains=search)
        query_params['search'] = search

    # Sort By
    sort_by = request.GET.get('sort_by', 'file')
    if sort_by not in ['file', 'file_type', 'size', 'uploaded_at']:
        sort_by = 'file'
    query_params['sort_by'] = sort_by

    # Order By
    order = request.GET.get('order', 'desc')
    if order == 'asc':
        qs = qs.order_by(sort_by)
        query_params['order'] = order
    else:
        qs = qs.order_by('-' + sort_by)
        query_params['order'] = order

    # File Type Filter
    file_type = request.GET.get('file_type', '')
    if file_type:
        qs = qs.filter(file_type=file_type)
        query_params['file_type'] = file_type

    # Public Filter
    public = request.GET.get('public', '')
    if public == 'true':
        qs = qs.filter(available_for_non_users=True)
        query_params['public'] = 'true'
    elif public == 'false':
        qs = qs.filter(available_for_non_users=False)
        query_params['public'] = 'false'

    querystring = urlencode(query_params)
    # Optimize file_types query - use only published files for filter dropdown
    file_types = Downloadable.objects.filter(status='published').values_list('file_type', flat=True).distinct()

    paginator = Paginator(qs, 2)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

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
  
    from shared.announcements.models import Announcement
    latest_announcements = Announcement.objects.filter(
        published_at__isnull=False,
        archived=False
    ).order_by('-published_at')[:2]

    return render(request, 'downloadables/user_downloadable.html', {
        'search': search,
        'sort_by': sort_by,
        'order': order,
        'file_type': file_type,
        'file_types': file_types,
        'public': public,
        'downloadables': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'page_range': page_range,
        'querystring': querystring,
        'latest_announcements': latest_announcements,
    })


@role_required(allowed_roles=["PROGRAM_HEAD", "DEAN", "COORDINATOR"], require_confirmed=True)
def superuser_downloadable(request):
    query_params = {}
    # Optimize with select_related
    qs = Downloadable.objects.filter(status='published').select_related('uploaded_by')

    # Search
    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(file__icontains=search)
        query_params['search'] = search

    # Sort By
    sort_by = request.GET.get('sort_by', 'file')
    if sort_by not in ['file', 'file_type', 'size', 'uploaded_at']:
        sort_by = 'file'
    query_params['sort_by'] = sort_by

    # Order By
    order = request.GET.get('order', 'desc')
    if order == 'asc':
        qs = qs.order_by(sort_by)
        query_params['order'] = order
    else:
        qs = qs.order_by('-' + sort_by)
        query_params['order'] = order

    # File Type Filter
    file_type = request.GET.get('file_type', '')
    if file_type:
        qs = qs.filter(file_type=file_type)
        query_params['file_type'] = file_type

    # Public Filter
    public = request.GET.get('public', '')
    if public == 'true':
        qs = qs.filter(available_for_non_users=True)
        query_params['public'] = 'true'
    elif public == 'false':
        qs = qs.filter(available_for_non_users=False)
        query_params['public'] = 'false'

    querystring = urlencode(query_params)
    file_types = Downloadable.objects.values_list('file_type', flat=True).distinct()

    paginator = Paginator(qs, 4)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

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

    return render(request, 'downloadables/superuser_downloadable.html', {
        'search': search,
        'sort_by': sort_by,
        'order': order,
        'file_type': file_type,
        'file_types': file_types,
        'public': public,
        'downloadables': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'page_range': page_range,
        'querystring': querystring,
    })


@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"], require_confirmed=True)
def admin_downloadable(request):
    query_params = {}
    # Optimize with select_related
    qs = Downloadable.objects.select_related('uploaded_by').all().order_by('-id')

    # Search
    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(file__icontains=search)
        query_params['search'] = search
    
    # Sort By
    sort_by = request.GET.get('sort_by', 'uploaded_at')
    if sort_by not in ['file', 'file_type', 'size', 'uploaded_at']:
        sort_by = 'uploaded_at'
    query_params['sort_by'] = sort_by

    # Order By
    order = request.GET.get('order', 'desc')
    query_params['order'] = order
    if order == 'asc':
        qs = qs.order_by(sort_by)
        query_params['order'] = order
    else:
        qs = qs.order_by('-' + sort_by)
        query_params['order'] = order

    # Status Filter
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)
        query_params['status'] = status

    # File Type Filter
    file_type = request.GET.get('file_type', '')
    if file_type:
        qs = qs.filter(file_type=file_type)
        query_params['file_type'] = file_type

    # Public Filter
    public = request.GET.get('public', '')
    if public == 'true':
        qs = qs.filter(available_for_non_users=True)
        query_params['public'] = 'true'
    elif public == 'false':
        qs = qs.filter(available_for_non_users=False)
        query_params['public'] = 'false'
        
    querystring = urlencode(query_params)

    # Optimize file_types query - get all file types for admin filter dropdown
    file_types = Downloadable.objects.values_list('file_type', flat=True).distinct().order_by('file_type')

    paginator = Paginator(qs, 4)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

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

    return render(request, 'downloadables/admin_downloadable.html', {
        'search': search,
        'sort_by': sort_by,
        'order': order,
        'status': status,
        'public': public,
        'file_type': file_type,
        'file_types': file_types,
        'downloadables': page_obj.object_list,
        'page_range': page_range,
        'page_obj': page_obj,
        'paginator': paginator,
        'querystring': querystring,
    })


@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"], require_confirmed=True)
def add_downloadable(request):
    error = None
    from .models import Downloadable
    submission_type_choices = Downloadable.SUBMISSION_TYPE_CHOICES
    if request.method == 'POST':
        form = DownloadableForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                downloadable = form.save(commit=False)
                downloadable.uploaded_by = request.user
                # Handle is_submission_template and submission_type from POST
                is_submission_template = request.POST.get('is_submission_template')
                downloadable.is_submission_template = bool(is_submission_template)
                submission_type = request.POST.get('submission_type')
                if submission_type in dict(downloadable.SUBMISSION_TYPE_CHOICES):
                    downloadable.submission_type = submission_type
                downloadable.save()
                from urllib.parse import quote
                return redirect(f'/downloadables/?success=true&action=created&name={quote(downloadable.name)}')
            except Exception as e:
                import logging
                logging.getLogger(__name__).exception("Error adding downloadable")
                error = 'An unexpected error occurred while saving this file.'
        else:
            error = form.errors.get('file', [''])[0] or 'Please correct the errors below.'
    else:
        form = DownloadableForm()
    return render(request, 'downloadables/add_downloadable.html', {'form': form, 'error': error, 'submission_type_choices': submission_type_choices})


# Download file
def downloadable_download(request, pk):
    from django.contrib import messages
    try:
        downloadable = Downloadable.objects.get(pk=pk)

        user = request.user
        user_role = getattr(user, 'role', None) if getattr(user, 'is_authenticated', False) else None
        admin_roles = {"UESO", "DIRECTOR", "VP"}

        # Access control: prevent IDOR via direct download URL
        if downloadable.status != 'published' and user_role not in admin_roles:
            raise Http404("Downloadable not found.")

        if not getattr(user, 'is_authenticated', False):
            if not downloadable.available_for_non_users or downloadable.status != 'published':
                raise Http404("Downloadable not found.")

        file_path = getattr(downloadable.file, 'path', None)
        if not file_path or not os.path.exists(file_path):
            # File missing on disk
            messages.error(request, "Sorry, this file is not available for download. Please contact the administrator.")
            return render(request, "downloadables/file_missing.html", {"file_name": getattr(downloadable, 'name', 'Unknown')})
        file_name = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        try:
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type=mime_type or 'application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{file_name}"'
                return response
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Error reading downloadable file")
            messages.error(request, "Error reading file.")
            return render(request, "downloadables/file_missing.html", {"file_name": file_name})
    except Downloadable.DoesNotExist:
        messages.error(request, "Downloadable file not found.")
        return render(request, "downloadables/file_missing.html", {"file_name": "Unknown"})


# Delete file
@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"], require_confirmed=True)
@require_POST
def downloadable_delete(request, pk):
    try:
        downloadable = Downloadable.objects.get(pk=pk)
        name = downloadable.name
        downloadable.file.delete(save=False)
        downloadable.delete()
        from urllib.parse import quote
        return redirect(f'/downloadables/?success=true&action=deleted&name={quote(name)}')
    except Downloadable.DoesNotExist:
        raise Http404("Downloadable not found.")


# Archive file
@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"], require_confirmed=True)
@require_POST
def downloadable_archive(request, pk):
    try:
        downloadable = Downloadable.objects.get(pk=pk)
        name = downloadable.name
        downloadable.status = 'archived'
        downloadable.save()
        from urllib.parse import quote
        return redirect(f'/downloadables/?success=true&action=archived&name={quote(name)}')
    except Downloadable.DoesNotExist:
        raise Http404("Downloadable not found.")


# Unarchive file
@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"], require_confirmed=True)
@require_POST
def downloadable_unarchive(request, pk):
    try:
        downloadable = Downloadable.objects.get(pk=pk)
        name = downloadable.name
        downloadable.status = 'published'
        downloadable.save()
        from urllib.parse import quote
        return redirect(f'/downloadables/?success=true&action=unarchived&name={quote(name)}')
    except Downloadable.DoesNotExist:
        raise Http404("Downloadable not found.")


# Make file public
@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"], require_confirmed=True)
@require_POST
def downloadable_make_public(request, pk):
    try:
        downloadable = Downloadable.objects.get(pk=pk)
        name = downloadable.name
        downloadable.available_for_non_users = True
        downloadable.save()
        from urllib.parse import quote
        return redirect(f'/downloadables/?success=true&action=made_public&name={quote(name)}')
    except Downloadable.DoesNotExist:
        raise Http404("Downloadable not found.")


# Make file private
@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"], require_confirmed=True)
@require_POST
def downloadable_make_private(request, pk):
    try:
        downloadable = Downloadable.objects.get(pk=pk)
        name = downloadable.name
        downloadable.available_for_non_users = False
        downloadable.save()
        from urllib.parse import quote
        return redirect(f'/downloadables/?success=true&action=made_private&name={quote(name)}')
    except Downloadable.DoesNotExist:
        raise Http404("Downloadable not found.")
