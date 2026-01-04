from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_api_key.models import APIKey
from system.settings.models import APIConnection

import logging

class APIKeyUserAuthentication(BaseAuthentication):
    """
    Authenticates the request using an API Key, but binds the request.user 
    to the 'requested_by' user of the APIConnection.
    """
    def authenticate(self, request):
        # Check for API Key header
        key = request.META.get("HTTP_AUTHORIZATION")
        if not key:
            # Try custom header if Authorization is not used
            key = request.META.get("HTTP_X_API_KEY")
            
        if not key:
            return None # Move to next authentication method

        # Remove "Api-Key " prefix if present (standard DRF format)
        if "Api-Key" in key:
            key = key.split(" ")[1]

        try:
            # Validate Key
            api_key = APIKey.objects.get_from_key(key)
            if not api_key:
                raise AuthenticationFailed("Invalid API Key")
            
            # Find the connection wrapper to get the owner
            try:
                conn = APIConnection.objects.get(api_key=api_key, status='ACTIVE')
            except APIConnection.DoesNotExist:
                raise AuthenticationFailed("API Connection is not active or does not exist.")

            # Bind User - check if requested_by column exists
            try:
                user = conn.requested_by
                if user is None:
                    raise AuthenticationFailed("API Connection has no associated user.")
                return (user, api_key)
            except Exception as e:
                # If requested_by_id column doesn't exist, return None to use next auth method
                if 'requested_by_id' in str(e) or 'no such column' in str(e).lower():
                    return None
                logging.getLogger(__name__).exception("Error accessing API Connection requested_by user")
                raise AuthenticationFailed("Error accessing API Connection user.")
            
        except Exception:
            return None