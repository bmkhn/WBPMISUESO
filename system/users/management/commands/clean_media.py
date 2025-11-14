from django.core.management.base import BaseCommand
from django.conf import settings
import os
import shutil


class Command(BaseCommand):
    help = 'Clean media folder by deleting specific subfolders and their contents'

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        
        self.stdout.write(self.style.WARNING(f'Fully wiping media folder: {media_root}'))
        deleted_count = 0
        error_count = 0

        # Delete everything inside media_root
        for item in os.listdir(media_root):
            item_path = os.path.join(media_root, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    self.stdout.write(self.style.SUCCESS(f'✓ Deleted folder: {item}/'))
                else:
                    os.remove(item_path)
                    self.stdout.write(self.style.SUCCESS(f'✓ Deleted file: {item}'))
                deleted_count += 1
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'✗ Error deleting {item}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'\n--- Media folder fully wiped ---'))
        self.stdout.write(f'Deleted: {deleted_count} items')
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
