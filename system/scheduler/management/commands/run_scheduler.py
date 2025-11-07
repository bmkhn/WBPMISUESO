# scheduler_app/management/commands/run_scheduler.py
from django.core.management.base import BaseCommand
from system.scheduler.scheduler import (
    publish_scheduled_announcements, 
    clear_expired_sessions, 
    update_event_statuses, 
    update_project_statuses, 
    update_user_expert_status
)

class Command(BaseCommand):
    help = 'Runs all recurring scheduler tasks one time for PythonAnywhere cron.'

    def handle(self, *args, **options):
        self.stdout.write("--- Running Centralized Scheduler Jobs ---")
        
        # 1. Run the Hourly/Minutely Job
        self.stdout.write("Running: publish_scheduled_announcements...")
        publish_scheduled_announcements()

        self.stdout.write("Running: update_event_statuses...")
        update_event_statuses()
        
        self.stdout.write("Running: update_project_statuses...")
        update_project_statuses()
        
        self.stdout.write("Running: update_user_expert_status...")
        update_user_expert_status()
        
        self.stdout.write("Running: clear_expired_sessions...")
        clear_expired_sessions() # This calls 'clearsessions' command, which is safe.
        
        self.stdout.write(self.style.SUCCESS("--- All Centralized Scheduler Jobs Finished ---"))