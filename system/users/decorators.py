from django.http import HttpResponseForbidden

def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Not authenticated")
            if request.user.role not in allowed_roles:
                return HttpResponseForbidden("You do not have permission")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def user_confirmed(view_func):
    def wrapper(request, *args, **kwargs):
        # If it's a non-user, just pass through
        if not hasattr(request.user, 'is_confirmed'):
            return view_func(request, *args, **kwargs)
        # If it's a user, must be confirmed
        if not request.user.is_confirmed:
            return HttpResponseForbidden("User not confirmed")
        return view_func(request, *args, **kwargs)
    return wrapper
