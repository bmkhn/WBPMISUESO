# /home/UESOMIS/Visual/system/management/commands/run_all_scheduled_jobs.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from system.scheduler.scheduler import (
    publish_scheduled_announcements, 
    clear_expired_sessions, 
    update_event_statuses, 
    update_project_statuses, 
    update_user_expert_status
)

class Command(BaseCommand):
    help = 'Runs all recurring scheduler tasks based on the current time.'

    def handle(self, *args, **options):
        # Ensure we use an aware datetime object for comparison
        now = timezone.now()
        current_hour = now.hour
        current_minute = now.minute
        
        self.stdout.write(f"--- Running Consolidated Scheduler Jobs at {now.strftime('%Y-%m-%d %H:%M:%S')} UTC ---")

        # --- 1. Minutely / High-Frequency Task (Runs every 5 minutes) ---
        # publish_scheduled_announcements was originally set to run every minute.
        # Running it every 5 minutes is the best we can do with the task limitation.
        self.stdout.write("Checking: publish_scheduled_announcements...")
        publish_scheduled_announcements()

        # --- 2. Daily Tasks (Runs only once daily at midnight UTC) ---
        if current_hour == 0 and current_minute < 5: 
            # Check for 00:00 (Midnight) to 00:04 (The first 5-minute slot)
            self.stdout.write(self.style.WARNING("Triggering DAILY MIDNIGHT jobs..."))
            
            # 00:00: Event and Project Status Updates
            self.stdout.write("Running: update_event_statuses...")
            update_event_statuses()
            
            self.stdout.write("Running: update_project_statuses...")
            update_project_statuses()
            
            # 00:01: Expert Status Update
            # Running this job slightly later (e.g., in the 00:01-00:04 range) is acceptable.
            self.stdout.write("Running: update_user_expert_status...")
            update_user_expert_status()
            
        # --- 3. Session Cleanup Task (Runs only once daily at 3:00 AM UTC) ---
        if current_hour == 3 and current_minute < 5: 
            # Check for 03:00 to 03:04
            self.stdout.write(self.style.WARNING("Triggering DAILY 03:00 AM job..."))
            self.stdout.write("Running: clear_expired_sessions...")
            clear_expired_sessions()

        self.stdout.write(self.style.SUCCESS("--- Consolidated Job Finished ---"))