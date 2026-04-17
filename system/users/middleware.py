from django.utils.cache import patch_cache_control
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.core.cache import caches
from django.db.models.signals import post_save, post_delete
from django.apps import apps
from django.http import StreamingHttpResponse, FileResponse

class SmartCacheMiddleware(MiddlewareMixin):
    """
    SmartCacheMiddleware

    - Caches GET page responses for all users:
        * Anonymous users: 24h cache (configurable)
        * Logged-in users: per-user cache (configurable duration)
    - Automatically invalidates all cached pages on any model change (post_save/post_delete).
    - Skips caching for streaming and file responses (e.g., media/static files, BufferedReader/FileResponse), preventing serialization errors.
    - Does not cache non-GET requests.
    - For large systems, selective cache invalidation can be implemented for efficiency.
    """

    def __init__(self, get_response=None):
        """
        Initialize SmartCacheMiddleware, set cache, timeouts, and connect model signals for cache invalidation.
        """
        super().__init__(get_response)
        self.cache = caches['default']
        self.anonymous_timeout = getattr(settings, 'CACHE_MIDDLEWARE_SECONDS', 86400)
        self.logged_in_timeout = getattr(settings, 'USER_CACHE_SECONDS', 600)
        self.cache_bypass_prefixes = tuple(getattr(settings, 'SMART_CACHE_BYPASS_PREFIXES', (
            '/oauth/',
            '/login/',
            '/logout/',
            '/register/',
            '/verify-login-2fa/',
            '/send-verification-code/',
            '/send-password-reset-code/',
            '/verify-reset-code/',
            '/reset-password/',
            '/forgot-password/',
            '/complete-profile/',
            '/select-role/',
            '/google-cancel/',
            '/admin/',
            '/static/',
            '/media/',
        )))
        self._connect_signals()


    def _connect_signals(self):
        """
        Connect post_save and post_delete signals for all models to cache invalidation handler.
        """
        for model in apps.get_models():
            post_save.connect(self._invalidate_cache, sender=model, dispatch_uid=f'invalidate_{model._meta.label}_save')
            post_delete.connect(self._invalidate_cache, sender=model, dispatch_uid=f'invalidate_{model._meta.label}_delete')


    def _invalidate_cache(self, sender, **kwargs):
        """
        Clears all cached pages for both anonymous and logged-in users.
        For large systems, consider selective invalidation for efficiency.
        """
        try:
            if hasattr(self.cache, 'delete_pattern'):
                self.cache.delete_pattern('anon:*')
                self.cache.delete_pattern('user:*')
                return

            if hasattr(self.cache, 'keys'):
                keys = [key for key in self.cache.keys('anon:*')] + [key for key in self.cache.keys('user:*')]
                for key in keys:
                    self.cache.delete(key)
                return

            self.cache.clear()
        except Exception:
            self.cache.clear()


    def _should_bypass_cache(self, request):
        """Skip cache for auth/session-sensitive and non-cacheable paths."""
        path = request.path or '/'
        return any(path.startswith(prefix) for prefix in self.cache_bypass_prefixes)


    def process_request(self, request):
        """
        Handles caching for GET requests only. Skips caching for non-GET requests.
        Returns cached response if available, otherwise allows view to process.
        """
        if request.method != "GET" or self._should_bypass_cache(request):
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
        """
        Caches GET responses unless they are streaming/file responses. 
        Skips caching for media/static files and handles serialization errors gracefully.
        """
        if request.method != "GET" or self._should_bypass_cache(request):
            return response

        if not getattr(request, '_cache_update_cache', True):
            return response

        if response.status_code != 200:
            return response

        if isinstance(response, (StreamingHttpResponse, FileResponse)):
            return response

        if response.has_header('Set-Cookie'):
            return response

        cache_control = (response.get('Cache-Control') or '').lower()
        if 'no-store' in cache_control or 'private' in cache_control:
            return response

        key = self._generate_cache_key(request)
        timeout = self.anonymous_timeout if not request.user.is_authenticated else self.logged_in_timeout
        try:
            self.cache.set(key, response, timeout=timeout)
        except Exception:
            pass

        return response


    def _generate_cache_key(self, request):
        """
        Generate cache key for request:
        - Anonymous: anon:<full_path>
        - Logged-in: user:<user_id>:<full_path>
        """
        if request.user.is_authenticated:
            return f"user:{request.user.id}:{request.get_full_path()}"
        return f"anon:{request.get_full_path()}"