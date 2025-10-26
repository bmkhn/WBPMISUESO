"""
Context processor to add unread notification count to all templates
"""

def unread_notifications(request):
    """
    Add unread notification count to template context
    """
    if request.user.is_authenticated:
        from .models import Notification
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}
