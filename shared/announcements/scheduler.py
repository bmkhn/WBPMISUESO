from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from django.core.management import call_command


def publish_scheduled_announcements():
    """
    Check and publish announcements that are scheduled and past their scheduled time.
    Runs every minute to ensure announcements are published on time.
    """
    from .models import Announcement
    from system.logs.models import LogEntry
    from django.urls import reverse
    
    now = timezone.now()
    
    # Find announcements that are scheduled and past their scheduled time
    scheduled_announcements = Announcement.objects.filter(
        is_scheduled=True,
        scheduled_at__lte=now,
        published_at__isnull=True
    )
    
    count = 0
    for announcement in scheduled_announcements:
        try:
            # Publish the announcement
            announcement.is_scheduled = False
            announcement.published_at = now
            announcement.published_by = announcement.scheduled_by
            
            # Set flag to skip duplicate log entries from signal
            announcement._skip_log = True
            announcement.save()
            
            # Create log entry for notification system
            url = reverse('announcement_details', args=[announcement.id])
            LogEntry.objects.create(
                user=announcement.published_by,
                action='CREATE',
                model='Announcement',
                object_id=announcement.id,
                object_repr=announcement.title,
                details="A new announcement has been published",
                url=url,
                is_notification=True
            )
            
            print(f"✓ Auto-published: {announcement.title}")
            count += 1
            
        except Exception as e:
            print(f"✗ Failed to publish announcement '{announcement.title}': {str(e)}")
    
    if count > 0:
        print(f"✓ Published {count} scheduled announcement(s) at {now.strftime('%Y-%m-%d %H:%M:%S')}")


def clear_expired_sessions():
    """
    Clear expired sessions from database.
    Runs daily to clean up old session data.
    """
    try:
        call_command('clearsessions')
        print(f"✓ Cleared expired sessions at {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"✗ Failed to clear sessions: {str(e)}")


def start_scheduler():
    """
    Start the background scheduler for announcements and maintenance tasks.
    This runs when Django starts up.
    """
    scheduler = BackgroundScheduler()
    
    # Run publish_scheduled_announcements every minute
    scheduler.add_job(
        publish_scheduled_announcements,
        'interval',
        minutes=1,
        id='publish_announcements',
        replace_existing=True,
        max_instances=1  # Prevent overlapping runs
    )
    
    # Clear expired sessions daily at 3:00 AM
    scheduler.add_job(
        clear_expired_sessions,
        'cron',
        hour=3,
        minute=0,
        id='clear_sessions',
        replace_existing=True
    )
    
    scheduler.start()
    print("✓ Scheduler started:")
    print("  - Announcements: checking every minute")
    print("  - Session cleanup: daily at 3:00 AM")
    
    # Schedule an immediate check 5 seconds after startup (after Django is fully ready)
    scheduler.add_job(
        publish_scheduled_announcements,
        'date',
        run_date=timezone.now() + timedelta(seconds=5),
        id='publish_announcements_startup',
        replace_existing=True
    )
