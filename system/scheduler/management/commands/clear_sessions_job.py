from django.core.management.base import BaseCommand
from system.scheduler.scheduler import clear_expired_sessions

class Command(BaseCommand):
    help = 'Runs the clearsessions command to remove expired Django sessions.'

    def handle(self, *args, **options):
        self.stdout.write("Running: clear_expired_sessions...")
        clear_expired_sessions()
        self.stdout.write(self.style.SUCCESS("Session cleanup complete."))