from celery import shared_task
from django.utils import timezone
from shared.announcements.models import Announcement

@shared_task
def publish_scheduled_announcements():
    now = timezone.now()
    scheduled = Announcement.objects.filter(is_scheduled=True, scheduled_at__lte=now, published_at__isnull=True)
    count = 0
    for ann in scheduled:
        ann.published_at = now
        ann.is_scheduled = False
        ann.save()
        count += 1
    return f'Published {count} scheduled announcements.'
