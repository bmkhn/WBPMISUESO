from django.core.management.base import BaseCommand
from system.scheduler.scheduler import update_project_statuses

class Command(BaseCommand):
    help = 'Updates project statuses (e.g., NOT_STARTED -> IN_PROGRESS) based on dates.'

    def handle(self, *args, **options):
        self.stdout.write("Running: update_project_statuses...")
        update_project_statuses()
        self.stdout.write(self.style.SUCCESS("Project status update complete."))