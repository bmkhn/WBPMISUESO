from rest_framework import permissions
from system.settings.models import APIConnection

class TieredAPIPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.auth:
            return False # Must be authenticated via API Key

        try:
            conn = APIConnection.objects.get(api_key=request.auth)
        except APIConnection.DoesNotExist:
            return False

        # 2. Enforce Tiers
        tier = conn.tier
        method = request.method
        
        # TIER 1: Read Projects Only
        if tier == 'TIER_1':
            if method not in permissions.SAFE_METHODS:
                return False
            if 'project' in request.path or 'analytics' in request.path:
                return True
            return False

        # TIER 2: Read All APIs
        if tier == 'TIER_2':
            if method in permissions.SAFE_METHODS:
                return True
            return False

        # TIER 3: Full Access
        if tier == 'TIER_3':
            if 'project' in request.path and method not in permissions.SAFE_METHODS:
                return False
            
            # Otherwise allow everything
            return True

        return False