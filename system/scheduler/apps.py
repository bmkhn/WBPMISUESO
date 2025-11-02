from django.apps import AppConfig


class SchedulerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'system.scheduler'
    scheduler_started = False

    def ready(self):
        """
        Start the centralized scheduler when Django starts.
        Only runs when the server is started, not during migrations or other management commands.
        """
        import sys
        import os
        
        # Only run in the main process, not the reloader process
        # Django runserver spawns two processes: parent (reloader) and child (actual server)
        # We only want to run scheduler in the child process
        if os.environ.get('RUN_MAIN') != 'true':
            return
        
        # Only start scheduler when running the server (not during migrations, makemigrations, etc.)
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
            # Prevent duplicate scheduler starts
            if not SchedulerConfig.scheduler_started:
                SchedulerConfig.scheduler_started = True
                
                # Delay scheduler start until after Django is fully initialized
                import threading
                threading.Timer(3.0, self._start_scheduler).start()
    

    def _start_scheduler(self):
        """Start the scheduler after Django is fully ready"""
        try:
            from . import scheduler
            scheduler.start_scheduler()
        except Exception as e:
            print(f"✗ Failed to start centralized scheduler: {e}")
