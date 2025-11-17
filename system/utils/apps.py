"""
System utilities app for cache management and signals.
"""

from django.apps import AppConfig


class UtilsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'system.utils'
    
    def ready(self):
        """
        Import signals when the app is ready.
        This ensures cache invalidation signals are registered.
        """
        import system.utils.signals
