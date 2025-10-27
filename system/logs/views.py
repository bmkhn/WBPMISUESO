from django.shortcuts import render
from system.users.decorators import role_required
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import LogEntry
from system.users.models import User

@role_required(allowed_roles=["VP", "DIRECTOR"], require_confirmed=True)
def logs_view(request):
    # Get filter parameters
    sort_by = request.GET.get('sort_by', 'timestamp')
    order = request.GET.get('order', 'desc')
    user_role = request.GET.get('user_role', '')
    action = request.GET.get('action', '')
    model = request.GET.get('model', '')
    search = request.GET.get('search', '').strip()
    
    # Base queryset
    logs = LogEntry.objects.select_related('user')
    
    # Apply filters
    if user_role:
        logs = logs.filter(user__role=user_role)
    if action:
        logs = logs.filter(action=action)
    if model:
        logs = logs.filter(model=model)
    if search:
        # Search in user name, email, and object_repr
        logs = logs.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(object_repr__icontains=search)
        )
    
    # Sorting
    sort_map = {
        'timestamp': 'timestamp',
        'user': 'user__first_name',
        'action': 'action',
        'model': 'model',
        'object_id': 'object_id',
        'object_repr': 'object_repr',
    }
    sort_field = sort_map.get(sort_by, 'timestamp')
    if order == 'desc':
        sort_field = '-' + sort_field
    logs = logs.order_by(sort_field)
    
    # Get filter options
    user_roles = User.Role.choices
    action_choices = LogEntry.ACTION_CHOICES
    # Get distinct models from logs
    models_list = LogEntry.objects.values_list('model', flat=True).distinct().order_by('model')
    
    # Pagination
    paginator = Paginator(logs, 10)
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
    
    return render(request, 'logs/logs.html', {
        'logs': page_obj,
        'user_roles': user_roles,
        'action_choices': action_choices,
        'models_list': models_list,
        'sort_by': sort_by,
        'order': order,
        'user_role': user_role,
        'action': action,
        'model': model,
        'search': search,
        'page_obj': page_obj,
        'paginator': paginator,
        'page_range': page_range,
        'querystring': request.GET.urlencode().replace('&page='+str(page_obj.number), '') if page_obj else '',
    })