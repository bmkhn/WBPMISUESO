from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.urls import reverse
from .forms import DownloadableForm
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from system.users.decorators import role_required
from django.core.paginator import Paginator
from .models import Downloadable
import mimetypes
import os


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
    if user.is_authenticated:
        # Faculty/Client: see all published files except archived
        qs = Downloadable.objects.filter(status='published')
    else:
        # Non-users: only see files available for public
        qs = Downloadable.objects.filter(status='published', available_for_non_users=True)

    # Search by file name
    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(file__icontains=search)

    # File Type Filter
    file_type = request.GET.get('file_type', '')
    if file_type:
        qs = qs.filter(file_type=file_type)

    # Date Filter
    date = request.GET.get('date', '')
    if date:
        qs = qs.filter(uploaded_at__date=date)

    # Sort By
    sort_by = request.GET.get('sort_by', 'file')
    if sort_by not in ['file', 'file_type', 'size', 'uploaded_at']:
        sort_by = 'file'

    # Order By
    order = request.GET.get('order', 'desc')
    if order == 'asc':
        qs = qs.order_by(sort_by)
    else:
        qs = qs.order_by('-' + sort_by)

    # Build querystring for pagination/filter links
    query_params = {}
    if search:
        query_params['search'] = search
    if file_type:
        query_params['file_type'] = file_type
    if date:
        query_params['date'] = date
    query_params['sort_by'] = sort_by
    query_params['order'] = order
    from urllib.parse import urlencode
    querystring = urlencode(query_params)

    # Get all file types for filter dropdown
    file_types = Downloadable.objects.values_list('file_type', flat=True).distinct()

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

    # Get 2 most recent announcements
    from shared.announcements.models import Announcement
    latest_announcements = Announcement.objects.filter(published_at__isnull=False).order_by('-published_at')[:2]

    return render(request, 'downloadables/user_downloadable.html', {
        'search': search,
        'file_type': file_type,
        'file_types': file_types,
        'date': date,
        'sort_by': sort_by,
        'order': order,
        'downloadables': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'page_range': page_range,
        'querystring': querystring,
        'latest_announcements': latest_announcements,
    })


@login_required
@role_required(allowed_roles=["PROGRAM_HEAD", "DEAN", "COORDINATOR"])
def superuser_downloadable(request):
    qs = Downloadable.objects.filter(status='published')

    # Search by file name
    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(file__icontains=search)

    # File Type Filter
    file_type = request.GET.get('file_type', '')
    if file_type:
        qs = qs.filter(file_type=file_type)

    # Date Filter
    date = request.GET.get('date', '')
    if date:
        qs = qs.filter(uploaded_at__date=date)

    # Sort By
    sort_by = request.GET.get('sort_by', 'file')
    if sort_by not in ['file', 'file_type', 'size', 'uploaded_at']:
        sort_by = 'file'

    # Order By
    order = request.GET.get('order', 'desc')
    if order == 'asc':
        qs = qs.order_by(sort_by)
    else:
        qs = qs.order_by('-' + sort_by)

    # Build querystring for pagination/filter links
    query_params = {}
    if search:
        query_params['search'] = search
    if file_type:
        query_params['file_type'] = file_type
    if date:
        query_params['date'] = date
    query_params['sort_by'] = sort_by
    query_params['order'] = order
    from urllib.parse import urlencode
    querystring = urlencode(query_params)

    # Get all file types for filter dropdown
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
        'file_type': file_type,
        'file_types': file_types,
        'date': date,
        'sort_by': sort_by,
        'order': order,
        'downloadables': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'page_range': page_range,
        'querystring': querystring,
    })


@login_required
@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"])
def admin_downloadable(request):
    qs = Downloadable.objects.all().order_by('-id')
    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(file__icontains=search)

    # Collect query params for querystring
    query_params = {}
    sort_by = request.GET.get('sort_by', 'uploaded_at')
    if sort_by not in ['file', 'file_type', 'size', 'uploaded_at']:
        sort_by = 'uploaded_at'
    query_params['sort_by'] = sort_by

    order = request.GET.get('order', 'desc')
    query_params['order'] = order
    if order == 'asc':
        qs = qs.order_by(sort_by)
    else:
        qs = qs.order_by('-' + sort_by)

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)
        query_params['status'] = status

    public = request.GET.get('public', '')
    if public == 'true':
        qs = qs.filter(available_for_non_users=True)
        query_params['public'] = 'true'
    elif public == 'false':
        qs = qs.filter(available_for_non_users=False)
        query_params['public'] = 'false'

    # File Type Filter
    file_type = request.GET.get('file_type', '')
    if file_type:
        qs = qs.filter(file_type=file_type)
        query_params['file_type'] = file_type

    date = request.GET.get('date', '')
    if date:
        qs = qs.filter(uploaded_at__date=date)
        query_params['date'] = date

    if search:
        query_params['search'] = search

    # Build querystring for pagination/filter links
    from urllib.parse import urlencode
    querystring = urlencode(query_params)

    # Get all file types for filter dropdown
    file_types = Downloadable.objects.values_list('file_type', flat=True).distinct()

    paginator = Paginator(qs, 5)
    page_number = request.GET.get('page')
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
        'date': date,
        'file_type': file_type,
        'file_types': file_types,
        'downloadables': page_obj.object_list,
        'page_range': page_range,
        'page_obj': page_obj,
        'paginator': paginator,
        'querystring': querystring,
    })

@login_required
@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"])
def add_downloadable(request):
    success = False
    error = ''
    form = DownloadableForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('downloadable_dispatcher'))
        else:
            error = form.errors.get('file', [''])[0] or 'Please correct the errors below.'
    return render(request, 'downloadables/add_downloadable.html', {'form': form, 'success': success, 'error': error})


# Download file
def downloadable_download(request, pk):
    try:
        downloadable = Downloadable.objects.get(pk=pk)
        file_path = downloadable.file.path
        file_name = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=mime_type or 'application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
    except Exception:
        raise Http404("File not found.")


# Delete file
@login_required
@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"])
def downloadable_delete(request, pk):
    try:
        downloadable = Downloadable.objects.get(pk=pk)
        downloadable.file.delete(save=False)
        downloadable.delete()
        return HttpResponseRedirect(reverse('downloadable_dispatcher'))
    except Downloadable.DoesNotExist:
        raise Http404("Downloadable not found.")


# Archive file
@login_required
@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"])
def downloadable_archive(request, pk):
    try:
        downloadable = Downloadable.objects.get(pk=pk)
        downloadable.status = 'archived'
        downloadable.save()
        return HttpResponseRedirect(reverse('downloadable_dispatcher'))
    except Downloadable.DoesNotExist:
        raise Http404("Downloadable not found.")


# Unarchive file
@login_required
@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"])
def downloadable_unarchive(request, pk):
    try:
        downloadable = Downloadable.objects.get(pk=pk)
        downloadable.status = 'published'
        downloadable.save()
        return HttpResponseRedirect(reverse('downloadable_dispatcher'))
    except Downloadable.DoesNotExist:
        raise Http404("Downloadable not found.")


# Make file public
@login_required
@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"])
def downloadable_make_public(request, pk):
    try:
        downloadable = Downloadable.objects.get(pk=pk)
        downloadable.available_for_non_users = True
        downloadable.save()
        return HttpResponseRedirect(reverse('downloadable_dispatcher'))
    except Downloadable.DoesNotExist:
        raise Http404("Downloadable not found.")


# Make file private
@login_required
@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"])
def downloadable_make_private(request, pk):
    try:
        downloadable = Downloadable.objects.get(pk=pk)
        downloadable.available_for_non_users = False
        downloadable.save()
        return HttpResponseRedirect(reverse('downloadable_dispatcher'))
    except Downloadable.DoesNotExist:
        raise Http404("Downloadable not found.")
