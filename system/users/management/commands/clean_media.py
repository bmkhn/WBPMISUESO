from django.core.management.base import BaseCommand
from django.conf import settings
import os
import shutil


class Command(BaseCommand):
    help = 'Clean media folder by deleting specific subfolders and their contents'

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        
        # Folders to DELETE
        folders_to_delete = [
            'about_us',
            'client_requests',
            'projects',
            'submissions',
            'users',
        ]
        
        # Folders to KEEP (these will not be deleted)
        # - colleges/logos/*
        # - default/*
        # - downloadables/files/*
        # - faker/*
        
        deleted_count = 0
        error_count = 0
        
        self.stdout.write(self.style.WARNING(f'Cleaning media folder: {media_root}'))
        self.stdout.write(self.style.WARNING('The following folders will be DELETED:'))
        for folder in folders_to_delete:
            self.stdout.write(f'  - {folder}/')
        
        self.stdout.write(self.style.SUCCESS('\nThe following folders will be KEPT:'))
        self.stdout.write('  - colleges/logos/*')
        self.stdout.write('  - default/*')
        self.stdout.write('  - downloadables/files/*')
        self.stdout.write('  - faker/*')
        
        for folder in folders_to_delete:
            folder_path = os.path.join(media_root, folder)
            
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                try:
                    # Delete the folder and all its contents
                    shutil.rmtree(folder_path)
                    deleted_count += 1
                    self.stdout.write(self.style.SUCCESS(f'✓ Deleted: {folder}/'))
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'✗ Error deleting {folder}/: {str(e)}'))
            else:
                self.stdout.write(self.style.WARNING(f'⊘ Skipped (not found): {folder}/'))
        
        self.stdout.write(self.style.SUCCESS(f'\n--- Cleanup Complete ---'))
        self.stdout.write(f'Deleted: {deleted_count} folders')
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
