"""
Custom middleware for session and security management
"""
from django.utils import timezone
from django.contrib.auth import logout
from django.shortcuts import redirect
from datetime import timedelta


class SessionSecurityMiddleware:
    """
    Enhanced session security middleware
    - Tracks last activity time
    - Enforces absolute session timeout
    - Detects suspicious session changes
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Skip processing for unauthenticated users
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Get current time
        now = timezone.now()
        
        # Check absolute session timeout (max 24 hours regardless of activity)
        session_start = request.session.get('session_start_time')
        if session_start:
            session_start_dt = timezone.datetime.fromisoformat(session_start)
            session_age = (now - session_start_dt).total_seconds()
            
            # Absolute timeout: 24 hours (86400 seconds)
            if session_age > 86400:
                logout(request)
                return redirect('/login/?timeout=absolute')
        else:
            # First request in this session, record start time
            request.session['session_start_time'] = now.isoformat()
        
        # Update last activity time
        request.session['last_activity'] = now.isoformat()
        
        # Security: Detect if user's role or status changed
        # (e.g., account was deactivated or role was modified by admin)
        if request.user.is_authenticated:
            cached_role = request.session.get('user_role')
            cached_confirmed = request.session.get('user_confirmed')
            
            if cached_role is None:
                # First time, cache the values
                request.session['user_role'] = request.user.role
                request.session['user_confirmed'] = request.user.is_confirmed
            else:
                # Check if user's permissions changed
                if (cached_role != request.user.role or 
                    cached_confirmed != request.user.is_confirmed or
                    not request.user.is_active):
                    # User's status changed - force re-login
                    logout(request)
                    return redirect('/login/?message=permissions_changed')
        
        response = self.get_response(request)
        return response


class RoleBasedSessionMiddleware:
    """
    Adjust session timeout based on user role
    - Higher privilege roles (VP, DIRECTOR) get longer sessions
    - Regular users get standard timeouts
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if request.user.is_authenticated:
            # Define role-based session timeouts (in seconds)
            # All roles now have 24 hours (86400 seconds)
            role_timeouts = {
                'VP': 86400,        # 24 hours
                'DIRECTOR': 86400,  # 24 hours
                'UESO': 86400,      # 24 hours
                'DEAN': 86400,      # 24 hours
                'PROGRAM_HEAD': 86400,  # 24 hours
                'COORDINATOR': 86400,   # 24 hours
                'FACULTY': 86400,       # 24 hours
                'IMPLEMENTER': 86400,   # 24 hours
                'CLIENT': 86400,        # 24 hours
            }
            
            user_role = getattr(request.user, 'role', None)
            if user_role in role_timeouts:
                # Set session age based on role
                request.session.set_expiry(role_timeouts[user_role])
        
        response = self.get_response(request)
        return response
