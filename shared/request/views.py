from django.shortcuts import render, redirect, get_object_or_404
from shared.request.models import ClientRequest
from system.users.decorators import role_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse
from .models import RequestUpdate


@role_required(allowed_roles=["UESO", "VP", "DIRECTOR", "CLIENT"])
def request_dispatcher(request):
    if request.user.role == 'CLIENT':
        return request_client_view(request)
    elif request.user.role in ['UESO', 'VP', 'DIRECTOR']:
        return request_admin_view(request)



@role_required(allowed_roles=["UESO", "VP", "DIRECTOR", "CLIENT"])
def request_details_dispatcher(request, pk):
    # Only allow the submitter or privileged roles to view
    req = get_object_or_404(ClientRequest, pk=pk)

    updates_qs = RequestUpdate.objects.filter(user=request.user).order_by('-updated_at')[:10]
    updates = []
    for update in updates_qs:
        status_text = {
            'UNDER_REVIEW': 'is being reviewed',
            'APPROVED': 'has been approved',
            'REJECTED': 'has been rejected',
            'ENDORSED': 'has been endorsed',
            'DENIED': 'has been denied',
        }.get(update.status, f'status updated to {update.status}')
        updates.append({
            'request_id': update.request.id,
            'title': update.request.title,
            'status': update.status,
            'viewed': update.viewed,
            'updated_at': update.updated_at,
            'message': f"Your request {update.request.title} {status_text}",
        })

    if request.user == req.submitted_by or request.user.role in ['UESO', 'VP', 'DIRECTOR']:
        if request.user.role == 'CLIENT':
            from django.urls import reverse
            from django.http import HttpResponseRedirect
            updated = RequestUpdate.objects.filter(user=request.user, request=req, viewed=False).update(viewed=True)
            if updated and request.method == 'GET' and not request.GET.get('new'):
                url = reverse('request_details_dispatcher', args=[pk])
                params = request.GET.copy()
                params['new'] = '1'
                url += '?' + params.urlencode()
                return HttpResponseRedirect(url)
            return render(request, 'request/request_client_details.html', {'req': req, 'my_updates': updates})
        else:
            return render(request, 'request/request_admin_details.html', {'req': req})
    return redirect('request_dispatcher')


########################################################################################################################



@role_required(allowed_roles=["CLIENT"])
def request_client_view(request):
    # Get recent status updates for this user's requests
    updates_qs = RequestUpdate.objects.filter(user=request.user).order_by('-updated_at')[:10]
    updates = []
    for update in updates_qs:
        # Build message text
        status_text = {
            'UNDER_REVIEW': 'is being reviewed',
            'APPROVED': 'has been approved',
            'REJECTED': 'has been rejected',
            'ENDORSED': 'has been endorsed',
            'DENIED': 'has been denied',
        }.get(update.status, f'status updated to {update.status}')
        updates.append({
            'request_id': update.request.id,
            'title': update.request.title,
            'status': update.status,
            'viewed': update.viewed,
            'updated_at': update.updated_at,
            'message': f"Your request {update.request.title} {status_text}",
        })

    from urllib.parse import urlencode
    requests = ClientRequest.objects.filter(submitted_by=request.user)
    query_params = {}

    # Filters
    sort_by = request.GET.get('sort_by', 'updated_at')
    query_params['sort_by'] = sort_by
    order = request.GET.get('order', 'desc')
    query_params['order'] = order
    status = request.GET.get('status', '')
    if status:
        requests = requests.filter(status__iexact=status)
        query_params['status'] = status
    date = request.GET.get('date', '')
    if date:
        requests = requests.filter(submitted_at__date=date) | requests.filter(updated_at__date=date)
        requests = requests.distinct()
        query_params['date'] = date
    search = request.GET.get('search', '').strip()
    if search:
        requests = requests.filter(title__icontains=search)
        query_params['search'] = search

    # Sorting
    sort_map = {
        'updated_at': 'updated_at',
        'submitted_at': 'submitted_at',
        'status': 'status',
        'title': 'title',
    }
    if sort_by:
        sort_field = sort_map.get(sort_by, 'updated_at')
        if order == 'desc':
            sort_field = '-' + sort_field
        requests = requests.order_by(sort_field, '-updated_at', '-submitted_at')
    else:
        requests = requests.order_by('-updated_at', '-submitted_at')

    querystring = urlencode(query_params)

    # Pagination
    paginator = Paginator(requests, 5)
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

    return render(request, 'request/request_client.html', {
        'requests': page_obj.object_list,
        'search': search,
        'sort_by': sort_by,
        'order': order,
        'status': status,
        'date': date,
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
        'page_range': page_range,
        'querystring': querystring,
        'my_updates': updates,
    })



@role_required(allowed_roles=["CLIENT"])
def submit_request(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        organization = request.POST.get('organization')
        primary_location = request.POST.get('primary_location')
        primary_beneficiary = request.POST.get('primary_beneficiary')
        summary = request.POST.get('summary')
        letter_of_intent = request.FILES.get('letter_of_intent')

        new_request = ClientRequest.objects.create(
            title=title,
            organization=organization,
            primary_location=primary_location,
            primary_beneficiary=primary_beneficiary,
            summary=summary,
            letter_of_intent=letter_of_intent if letter_of_intent else None,
            status='RECEIVED',
            submitted_by=request.user,
            submitted_at=timezone.now()
        )
        new_request.save()

        return redirect('request_dispatcher')
    else:
        return redirect('request_dispatcher')


########################################################################################################################



@role_required(allowed_roles=["UESO", "VP", "DIRECTOR"])
def request_admin_view(request):
    from urllib.parse import urlencode
    requests = ClientRequest.objects.all()
    query_params = {}

    # Filters
    sort_by = request.GET.get('sort_by', 'updated_at')
    query_params['sort_by'] = sort_by
    order = request.GET.get('order', 'desc')
    query_params['order'] = order
    status = request.GET.get('status', '')
    if status:
        requests = requests.filter(status__iexact=status)
        query_params['status'] = status
    date = request.GET.get('date', '')
    if date:
        requests = requests.filter(deadline__date=date)
        query_params['date'] = date
    search = request.GET.get('search', '').strip()
    if search:
        requests = requests.filter(title__icontains=search)
        query_params['search'] = search

    requests = requests.distinct()

    # Sorting
    sort_map = {
        'updated_at': 'updated_at',
        'submitted_at': 'submitted_at',
        'status': 'status',
        'title': 'title',
    }
    if sort_by:
        sort_field = sort_map.get(sort_by, 'updated_at')
        if order == 'desc':
            sort_field = '-' + sort_field
        requests = requests.order_by(sort_field, '-updated_at', '-submitted_at')
    else:
        requests = requests.order_by('-updated_at', '-submitted_at')

    querystring = urlencode(query_params)

    # Pagination
    paginator = Paginator(requests, 10)
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

    return render(request, 'request/request_admin.html', {
        'requests': page_obj.object_list,
        'search': search,
        'sort_by': sort_by,
        'order': order,
        'status': status,
        'date': date,
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
        'page_range': page_range,
        'querystring': querystring,
    })


# APPROVE/REJECT/ENDORSE

@role_required(allowed_roles=["UESO", "VP", "DIRECTOR"])
def admin_request_action(request, pk):
    req = get_object_or_404(ClientRequest, pk=pk)
    from django.utils import timezone
    if request.method == 'POST':
        action = request.POST.get('action')
        if req.status == 'UNDER_REVIEW':
            if action == 'approve':
                req.status = 'APPROVED'
                req.reviewed_by = request.user
                req.review_at = timezone.now()
                req.updated_at = timezone.now()
                req.updated_by = request.user
                req.save()
            elif action == 'reject':
                req.status = 'REJECTED'
                req.reviewed_by = request.user
                req.review_at = timezone.now()
                req.updated_at = timezone.now()
                req.updated_by = request.user
                req.reason = request.POST.get('reason', '')
                req.save()
        elif req.status == 'APPROVED' and action == 'endorse':
            req.status = 'ENDORSED'
            req.endorsed_by = request.user
            req.endorsed_at = timezone.now()
            req.updated_at = timezone.now()
            req.updated_by = request.user
            req.save()
            
        # Create or update RequestUpdate for the submitter
        if req.submitted_by:
            RequestUpdate.objects.update_or_create(
                user=req.submitted_by,
                request=req,
                status=req.status,
                defaults={
                    'viewed': False,
                    'updated_at': req.updated_at,
                }
            )
    return redirect('request_details_dispatcher', pk=pk)



@role_required(allowed_roles=["UESO", "VP", "DIRECTOR"])
def admin_request_details_entry(request, pk):
    req = get_object_or_404(ClientRequest, pk=pk)
    if req.status == 'RECEIVED':
        req.status = 'UNDER_REVIEW'
        req.reviewed_by = request.user
        req.review_at = timezone.now()
        req.updated_by = request.user
        req.save()
    return redirect('request_details_dispatcher', pk=pk)
