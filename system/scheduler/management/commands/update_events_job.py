from django.core.management.base import BaseCommand
from system.scheduler.scheduler import update_event_statuses

class Command(BaseCommand):
    help = 'Updates event statuses (SCHEDULED/ONGOING/COMPLETED) based on dates.'

    def handle(self, *args, **options):
        self.stdout.write("Running: update_event_statuses...")
        update_event_statuses()
        self.stdout.write(self.style.SUCCESS("Event status update complete."))