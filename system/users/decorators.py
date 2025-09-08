from django.shortcuts import redirect

def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('not_authenticated')
            if request.user.role not in allowed_roles:
                return redirect('no_permission')
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
            return redirect('not_confirmed')
        return view_func(request, *args, **kwargs)
    return wrapper
