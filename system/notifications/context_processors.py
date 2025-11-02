"""
Context processor to add unread notification count to all templates
"""
from django.core.cache import cache

def unread_notifications(request):
    """
    Add unread notification count to template context
    Uses caching to avoid querying database on every page load
    """
    if request.user.is_authenticated:
        # Try to get count from cache first
        cache_key = f'unread_notif_count_{request.user.id}'
        unread_count = cache.get(cache_key)
        
        if unread_count is None:
            # Cache miss - query database
            from .models import Notification
            unread_count = Notification.objects.filter(
                recipient=request.user,
                is_read=False
            ).count()
            # Cache for 5 minutes (300 seconds)
            cache.set(cache_key, unread_count, 300)
        
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}
