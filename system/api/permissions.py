from rest_framework import permissions
from rest_framework_api_key.models import APIKey
from system.settings.models import APIConnection

class TieredAPIPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        key = request.META.get("HTTP_X_API_KEY")
        if not key:
            return False

        try:
            api_key = APIKey.objects.get_from_key(key)
            if not api_key:
                return False

            conn = APIConnection.objects.get(api_key=api_key, status='ACTIVE')
        except (APIConnection.DoesNotExist, APIKey.DoesNotExist):
            return False

        tier = conn.tier
        method = request.method
        path = request.path
        
        if tier == 'TIER_1':
            if method not in permissions.SAFE_METHODS:
                return False
            if 'project' in path or 'analytics' in path:
                return True
            return False

        if tier == 'TIER_2':
            if method in permissions.SAFE_METHODS:
                return True
            return False

        if tier == 'TIER_3':
            if 'project' in path and method not in permissions.SAFE_METHODS:
                return False
            return True

        return False