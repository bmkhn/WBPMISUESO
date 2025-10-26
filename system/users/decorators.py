from django.shortcuts import redirect

def role_required(allowed_roles, require_confirmed=False):
    """
    Decorator to restrict access to users with specific roles.
    Optionally requires the user to be confirmed.
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('not_authenticated')
            if require_confirmed:
                # If it's a non-user, just pass through
                if hasattr(request.user, 'is_confirmed') and not request.user.is_confirmed:
                    return redirect('not_confirmed')
            if request.user.role not in allowed_roles:
                return redirect('no_permission')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator