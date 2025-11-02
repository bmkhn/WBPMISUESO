from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
import sys


class Command(BaseCommand):
    help = "Completely reset the database - delete all data and optionally rebuild with test data"

    def handle(self, *args, **kwargs):
        self.stdout.write('\n' + self.style.WARNING('Starting database reset...'))
        
        # Step 1: Flush the database (delete all data)
        self.stdout.write('\n[1/2] Flushing database...')
        try:
            call_command('flush', '--no-input', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✓ Database flushed successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error flushing database: {e}'))
            return
        
        # Step 2: Clear migrations (optional - keeps migration history)
        self.stdout.write('\n[2/2] Checking migrations...')
        try:
            # Show current migration status
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM django_migrations")
                migration_count = cursor.fetchone()[0]
            self.stdout.write(self.style.SUCCESS(f'✓ {migration_count} migrations in history'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error checking migrations: {e}'))