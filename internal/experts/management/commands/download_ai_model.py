from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = "Download and cache the AI model for team generation"

    def handle(self, *args, **kwargs):
        if getattr(settings, 'PYTHONANYWHERE_VERSION', False):
            self.stdout.write(self.style.ERROR(
                getattr(
                    settings,
                    'PYTHONANYWHERE_UNAVAILABLE_MESSAGE',
                    'This is not available in the pythonanywhere version of the system',
                )
            ))
            return

        # Define model cache directory inside the Django project
        model_cache_dir = os.path.join(settings.BASE_DIR, 'internal', 'experts', 'ai_model')
        
        self.stdout.write(self.style.SUCCESS(f'Downloading AI model (all-MiniLM-L6-v2) to: {model_cache_dir}'))
        
        try:
            from sentence_transformers import SentenceTransformer

            # Ensure cache directory exists
            os.makedirs(model_cache_dir, exist_ok=True)
            
            # Download model to the specified cache folder
            model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder=model_cache_dir)
            
            self.stdout.write(self.style.SUCCESS('✓ Model downloaded and cached successfully!'))
            self.stdout.write(self.style.SUCCESS(f'✓ Model location: {model_cache_dir}'))
            self.stdout.write(self.style.SUCCESS('The AI team generator is ready to use.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to download model: {e}'))
