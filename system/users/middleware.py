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
        # Only act for authenticated users
        if request.user.is_authenticated:
            now = timezone.now()
            # Only check absolute timeout if session_start_time exists
            session_start = request.session.get('session_start_time')
            if session_start:
                session_start_dt = timezone.datetime.fromisoformat(session_start)
                session_age = (now - session_start_dt).total_seconds()
                if session_age > 86400:
                    # Only logout and flush session if timeout exceeded
                    logout(request)
                    return redirect('/login/?timeout=absolute')
            # Only set session_start_time if not present and not already being set by login
            elif not request.session.get('_just_logged_in'):
                request.session['session_start_time'] = now.isoformat()
            # Only update last_activity if not already being set by login
            if not request.session.get('_just_logged_in'):
                request.session['last_activity'] = now.isoformat()
            # Security: Detect if user's role or status changed
            cached_role = request.session.get('user_role')
            cached_confirmed = request.session.get('user_confirmed')
            if cached_role is not None:
                if (cached_role != request.user.role or 
                    cached_confirmed != request.user.is_confirmed or
                    not request.user.is_active):
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
        # Only set expiry on login, not every request
        if request.user.is_authenticated and request.session.get('_just_logged_in'):
            role_timeouts = {
                'VP': 86400,
                'DIRECTOR': 86400,
                'UESO': 86400,
                'DEAN': 86400,
                'PROGRAM_HEAD': 86400,
                'COORDINATOR': 86400,
                'FACULTY': 86400,
                'IMPLEMENTER': 86400,
                'CLIENT': 86400,
            }
            user_role = getattr(request.user, 'role', None)
            if user_role in role_timeouts:
                request.session.set_expiry(role_timeouts[user_role])
            # Remove the flag after setting expiry
            request.session.pop('_just_logged_in', None)
        response = self.get_response(request)
        return response
