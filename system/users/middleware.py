# myproject/middleware.py
from django.utils.cache import patch_cache_control
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.core.cache import caches
from django.db.models.signals import post_save, post_delete
from django.apps import apps

class SmartCacheMiddleware(MiddlewareMixin):
    """
    Caches pages for all users safely:
    - Anonymous pages: 24h cache
    - Logged-in pages: per-user cache (configurable duration)
    Automatically invalidates caches on model changes.
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.cache = caches['default']
        self.anonymous_timeout = getattr(settings, 'CACHE_MIDDLEWARE_SECONDS', 86400)
        self.logged_in_timeout = getattr(settings, 'USER_CACHE_SECONDS', 600)  
        self._connect_signals()

    def _connect_signals(self):
        """
        Connect signals to invalidate cache automatically.
        You can restrict which models trigger invalidation.
        """
        for model in apps.get_models():
            post_save.connect(self._invalidate_cache, sender=model, dispatch_uid=f'invalidate_{model._meta.label}_save')
            post_delete.connect(self._invalidate_cache, sender=model, dispatch_uid=f'invalidate_{model._meta.label}_delete')

    def _invalidate_cache(self, sender, **kwargs):
        """
        Clears the entire anonymous and user caches.
        For larger systems, selective invalidation can be implemented.
        """
        keys = [key for key in self.cache.keys("anon:*")] + [key for key in self.cache.keys("user:*")]
        for key in keys:
            self.cache.delete(key)

    def process_request(self, request):
        # Don't cache non-GET requests
        if request.method != "GET":
            request._cache_update_cache = False
            return None

        key = self._generate_cache_key(request)
        response = self.cache.get(key)
        if response:
            timeout = self.anonymous_timeout if not request.user.is_authenticated else self.logged_in_timeout
            patch_cache_control(response, max_age=timeout)
            return response

        request._cache_update_cache = True
        return None

    def process_response(self, request, response):
        # Only cache GET responses
        if getattr(request, '_cache_update_cache', True) and request.method == "GET":
            key = self._generate_cache_key(request)
            timeout = self.anonymous_timeout if not request.user.is_authenticated else self.logged_in_timeout
            self.cache.set(key, response, timeout=timeout)
        return response

    def _generate_cache_key(self, request):
        """
        Generate cache key:
        - Anonymous: anon:<full_path>
        - Logged-in: user:<user_id>:<full_path>
        """
        if request.user.is_authenticated:
            return f"user:{request.user.id}:{request.get_full_path()}"
        return f"anon:{request.get_full_path()}"