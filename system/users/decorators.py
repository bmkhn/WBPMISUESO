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