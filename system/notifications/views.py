from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Notification


def get_role_constants():
    ADMIN_ROLES = ["VP", "DIRECTOR", "UESO"]
    SUPERUSER_ROLES = ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]
    FACULTY_ROLE = ["FACULTY", "IMPLEMENTER"]
    COORDINATOR_ROLE = ["COORDINATOR"]
    return ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE


def get_templates(request):
    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"
    return base_template


@login_required
def notification_list(request):
    """Display list of notifications for the current user"""
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()
    base_template = get_templates(request)
    
    # Get filter parameter
    filter_type = request.GET.get('filter', 'all')  # all, unread, read
    
    # Get all notifications for the current user
    notifications = Notification.objects.filter(recipient=request.user).select_related('actor')
    
    # Apply filter
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_type == 'read':
        notifications = notifications.filter(is_read=True)
    
    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(notifications, 20)  # 20 notifications per page
    page_obj = paginator.get_page(page_number)
    
    # Count unread notifications (use cache)
    from django.core.cache import cache
    cache_key = f'unread_notif_count_{request.user.id}'
    unread_count = cache.get(cache_key)
    
    if unread_count is None:
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        cache.set(cache_key, unread_count, 300)

    context = {
        'base_template': base_template,
        'ADMIN_ROLES': ADMIN_ROLES,
        'SUPERUSER_ROLES': SUPERUSER_ROLES,
        'FACULTY_ROLE': FACULTY_ROLE,
        'COORDINATOR_ROLE': COORDINATOR_ROLE,
        'notifications': page_obj,
        'paginator': paginator,
        'page_obj': page_obj,
        'filter_type': filter_type,
        'unread_count': unread_count,
    }

    return render(request, 'notifications/notification_list.html', context)


@login_required
@require_POST
def mark_as_read(request, notification_id):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.mark_as_read()
    
    return JsonResponse({
        'success': True,
        'notification_id': notification_id,
        'is_read': notification.is_read
    })


@login_required
@require_POST
def mark_all_as_read(request):
    """Mark all notifications as read for the current user"""
    from django.utils import timezone
    from django.core.cache import cache
    now = timezone.now()
    
    # Update all unread notifications in a single query
    updated_count = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).update(
        is_read=True,
        read_at=now
    )
    
    # Invalidate cache so user sees updated count immediately
    cache_key = f'unread_notif_count_{request.user.id}'
    cache.delete(cache_key)
    
    return JsonResponse({
        'success': True,
        'message': f'{updated_count} notifications marked as read'
    })


@login_required
def get_unread_count(request):
    """Get count of unread notifications (for AJAX requests)"""
    from django.core.cache import cache
    
    # Try cache first
    cache_key = f'unread_notif_count_{request.user.id}'
    count = cache.get(cache_key)
    
    if count is None:
        # Cache miss - query database
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        cache.set(cache_key, count, 300)  # Cache for 5 minutes
    
    return JsonResponse({
        'count': count
    })


@login_required
def get_recent_notifications(request):
    """Get recent notifications (for dropdown/badge)"""
    from django.core.cache import cache
    
    limit = int(request.GET.get('limit', 5))
    
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('actor')[:limit]
    
    data = []
    for notif in notifications:
        data.append({
            'id': notif.id,
            'message': notif.get_message(),
            'url': notif.url,
            'is_read': notif.is_read,
            'created_at': notif.created_at.isoformat(),
            'actor': notif.actor.get_full_name() if notif.actor else 'System',
        })
    
    # Use cached count
    cache_key = f'unread_notif_count_{request.user.id}'
    unread_count = cache.get(cache_key)
    
    if unread_count is None:
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        cache.set(cache_key, unread_count, 300)
    
    return JsonResponse({
        'notifications': data,
        'unread_count': unread_count
    })
