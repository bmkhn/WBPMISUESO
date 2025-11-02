from django.core.management.base import BaseCommand
from django.utils import timezone
from shared.announcements.models import Announcement


class Command(BaseCommand):
    help = 'Manually publish scheduled announcements that are past their scheduled time'

    def handle(self, *args, **options):
        now = timezone.now()
        
        self.stdout.write(self.style.WARNING(f'Checking for scheduled announcements at {now.strftime("%Y-%m-%d %H:%M:%S")}...'))
        
        # Find announcements that are scheduled and past their scheduled time
        scheduled_announcements = Announcement.objects.filter(
            is_scheduled=True,
            scheduled_at__lte=now,
            published_at__isnull=True
        )
        
        count = scheduled_announcements.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING('⊙ No announcements ready to publish'))
            return
        
        self.stdout.write(self.style.WARNING(f'Found {count} announcement(s) to publish...\n'))
        
        # Publish each announcement
        published_count = 0
        for announcement in scheduled_announcements:
            try:
                old_status = f"Scheduled for {announcement.scheduled_at.strftime('%Y-%m-%d %H:%M')}"
                
                # Publish the announcement
                announcement.is_scheduled = False
                announcement.published_at = now
                announcement.published_by = announcement.scheduled_by
                
                # Set flag to skip duplicate log entries from signal
                announcement._skip_log = True
                announcement.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Published: "{announcement.title}"')
                )
                self.stdout.write(f'  {old_status} → Published at {now.strftime("%Y-%m-%d %H:%M")}')
                
                published_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error publishing "{announcement.title}": {str(e)}')
                )
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✓ Successfully published {published_count} of {count} announcement(s)'))
        self.stdout.write('='*60)
