from django.core.management.base import BaseCommand
from system.scheduler.scheduler import publish_scheduled_announcements

class Command(BaseCommand):
    help = 'Runs the announcement publication check, which runs every minute.'

    def handle(self, *args, **options):
        self.stdout.write("Running: publish_scheduled_announcements...")
        publish_scheduled_announcements()
        self.stdout.write(self.style.SUCCESS("Announcements check complete."))