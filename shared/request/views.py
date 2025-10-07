from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from shared.request.models import ClientRequest
from system.users.decorators import role_required
from django.utils import timezone
from django.core.paginator import Paginator


@login_required
@role_required(allowed_roles=["UESO", "VP", "DIRECTOR", "CLIENT"])
def request_dispatcher(request):
    if request.user.role == 'CLIENT':
        return render(request, 'request/request_client.html')
    elif request.user.role in ['UESO', 'VP', 'DIRECTOR']:
        return render(request, 'request/request_admin.html')


def request_client_view(request):
    return render(request, 'request/request_client.html')


def request_admin_view(request):
    requests = ClientRequest.objects.all()

    # Filters
    sort_by = request.GET.get('sort_by', 'date_submitted')
    order = request.GET.get('order', 'desc')
    status = request.GET.get('status', '')
    date = request.GET.get('date', '')
    search = request.GET.get('search', '').strip()

    # Apply filters
    if status: requests = requests.filter(status__iexact=status)
    if date: requests = requests.filter(deadline__date=date)
    if search: requests = requests.filter(projects__title__icontains=search)

    requests = requests.distinct()

    # Sorting
    sort_map = {
        'date_submitted': 'submitted_at',
        'status': 'status',
        'project': 'projects__title',
    }
    sort_field = sort_map.get(sort_by, 'date_submitted')
    if sort_field:
        if order == 'desc':
            sort_field = '-' + sort_field
        requests = requests.order_by(sort_field)

    # Filter Options
    all_statuses = [status[1] for status in ClientRequest.STATUS_CHOICES]

    # Pagination
    paginator = Paginator(requests, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(page_obj.number)

    return render(request, 'request/request_admin.html', {
        'search': search,
        'sort_by': sort_by,
        'order': order,
        'all_statuses': all_statuses,
        'status': status,
        'date': date,
        'page_obj': page_obj,
        'page_range': page_range,
        'querystring': request.GET.urlencode().replace('&page='+str(page_obj.number), '') if page_obj else '',
    })

