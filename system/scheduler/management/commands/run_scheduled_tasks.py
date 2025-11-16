from django.core.management.base import BaseCommand
from system.scheduler.scheduler import (
    publish_scheduled_announcements,
    clear_expired_sessions,
    update_event_statuses,
    update_project_statuses,
    update_user_expert_status,
    send_event_reminders
)


class Command(BaseCommand):
    help = 'Manually run scheduled tasks (for Railway CLI or testing)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            help='Specific task to run: announcements, sessions, events, projects, experts, reminders, or all (default)',
            default='all'
        )

    def handle(self, *args, **options):
        task = options['task'].lower()
        
        self.stdout.write(self.style.WARNING('\n🔧 Running scheduled tasks manually...\n'))
        
        if task in ['announcements', 'all']:
            self.stdout.write('📢 Publishing scheduled announcements...')
            publish_scheduled_announcements()
            self.stdout.write('')
        
        if task in ['sessions', 'all']:
            self.stdout.write('🗑️  Clearing expired sessions...')
            clear_expired_sessions()
            self.stdout.write('')
        
        if task in ['events', 'all']:
            self.stdout.write('📅 Updating event statuses...')
            update_event_statuses()
            self.stdout.write('')
        
        if task in ['projects', 'all']:
            self.stdout.write('📊 Updating project statuses...')
            update_project_statuses()
            self.stdout.write('')
        
        if task in ['experts', 'all']:
            self.stdout.write('👥 Updating user expert status...')
            update_user_expert_status()
            self.stdout.write('')
        
        if task in ['reminders', 'all']:
            self.stdout.write('📧 Sending event reminders...')
            send_event_reminders()
            self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('\n✅ All scheduled tasks completed!\n'))
        self.stdout.write(self.style.WARNING('💡 Usage examples:'))
        self.stdout.write('   python manage.py run_scheduled_tasks')
        self.stdout.write('   python manage.py run_scheduled_tasks --task=announcements')
        self.stdout.write('   python manage.py run_scheduled_tasks --task=reminders')
        self.stdout.write('   railway run python manage.py run_scheduled_tasks\n')
