from rest_framework import permissions
from system.settings.models import APIConnection
from rest_framework_api_key.models import APIKey

class TieredAPIPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # 1. Check User Authentication (Token)
        if not request.user or not request.user.is_authenticated:
            return False

        # 2. Check API Key (Tier)
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
        
        # TIER 1: Read Projects Only (and Analytics)
        if tier == 'TIER_1':
            if method not in permissions.SAFE_METHODS:
                return False
            if 'project' in path or 'analytics' in path:
                return True
            return False

        # TIER 2: Read All APIs
        if tier == 'TIER_2':
            if method in permissions.SAFE_METHODS:
                return True
            return False

        # TIER 3: Full Access
        if tier == 'TIER_3':
            return True

        return False