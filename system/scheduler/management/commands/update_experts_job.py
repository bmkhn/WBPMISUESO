from django.core.management.base import BaseCommand
from system.scheduler.scheduler import update_user_expert_status

class Command(BaseCommand):
    help = 'Updates user expert status for faculty based on project involvement.'

    def handle(self, *args, **options):
        self.stdout.write("Running: update_user_expert_status...")
        update_user_expert_status()
        self.stdout.write(self.style.SUCCESS("Expert status update complete."))