from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.urls import reverse
from .forms import DownloadableForm
from django.shortcuts import render
from system.users.decorators import role_required
from django.core.paginator import Paginator
from .models import Downloadable
import mimetypes
import os
from urllib.parse import urlencode


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
        # Faculty/Client: see all published files except archived
        qs = Downloadable.objects.filter(status='published')
    else:
        # Non-Users: only see files available for public
        qs = Downloadable.objects.filter(status='published', available_for_non_users=True)
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


@role_required(allowed_roles=["PROGRAM_HEAD", "DEAN", "COORDINATOR"])
def superuser_downloadable(request):
    query_params = {}
    qs = Downloadable.objects.filter(status='published')

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


@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"])
def admin_downloadable(request):
    query_params = {}
    qs = Downloadable.objects.all().order_by('-id')

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

    file_types = Downloadable.objects.values_list('file_type', flat=True).distinct()

    paginator = Paginator(qs, 5)
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


@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"])
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
                return render(request, 'downloadables/add_downloadable.html', {'form': DownloadableForm(), 'success': True, 'submission_type_choices': submission_type_choices})
            except Exception as e:
                error = str(e)
        else:
            error = form.errors.get('file', [''])[0] or 'Please correct the errors below.'
    else:
        form = DownloadableForm()
    return render(request, 'downloadables/add_downloadable.html', {'form': form, 'error': error, 'submission_type_choices': submission_type_choices})


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
@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"])
def downloadable_make_private(request, pk):
    try:
        downloadable = Downloadable.objects.get(pk=pk)
        downloadable.available_for_non_users = False
        downloadable.save()
        return HttpResponseRedirect(reverse('downloadable_dispatcher'))
    except Downloadable.DoesNotExist:
        raise Http404("Downloadable not found.")
