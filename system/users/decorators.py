from django.shortcuts import redirect, get_object_or_404, render
from django.http import HttpResponseForbidden

def role_required(allowed_roles, require_confirmed=False):
    """
    Decorator to restrict access to users with specific roles.
    Optionally requires the user to be confirmed.
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('not_authenticated')
            
            # Check if Google user needs profile completion (for protected features)
            from .views import is_google_profile_incomplete, is_google_account
            from .models import User
            
            if is_google_account(request.user):
                # Check if needs role selection
                if (request.user.role == User.Role.CLIENT and 
                    not request.user.email.lower().endswith('@psu.palawan.edu.ph') and
                    (request.user.given_name in ['Google', ''] or request.user.last_name in ['User', ''])):
                    return redirect('select_google_role')
                
                # Check if profile is incomplete
                if is_google_profile_incomplete(request.user):
                    return redirect('complete_google_profile')
            
            if require_confirmed:
                # If it's a non-user, just pass through
                if hasattr(request.user, 'is_confirmed') and not request.user.is_confirmed:
                    return redirect('not_confirmed')
            
            # Allow superusers to bypass role checks
            if getattr(request.user, 'is_superuser', False):
                response = view_func(request, *args, **kwargs)
                if response is None:
                    from django.http import HttpResponse
                    return HttpResponse("View did not return a response", status=500)
                return response
            
            # Safely check role - if user doesn't have role attribute or role is None, deny access
            user_role = getattr(request.user, 'role', None)
            if user_role not in allowed_roles:
                return redirect('no_permission')
            # Ensure we always return the view's response
            response = view_func(request, *args, **kwargs)
            if response is None:
                from django.http import HttpResponse
                return HttpResponse("View did not return a response", status=500)
            return response
        return wrapper
    return decorator


def project_visibility_required(view_func):
    """
    Decorator to check if a user can view a project based on visibility restrictions:
    - Non-authenticated users: only COMPLETED projects
    - Project leader/providers: can see their projects regardless of status
    - Dean/Coordinator/Program Head: can see all projects from their college
    - UESO/Director/VP: can see everything
    """
    def wrapper(request, *args, **kwargs):
        # Get project_id from URL kwargs (could be 'pk' or 'project_id')
        project_id = kwargs.get('pk') or kwargs.get('project_id')
        
        if project_id:
            from shared.projects.models import Project
            project = get_object_or_404(Project, pk=project_id)
            
            # Check if user can view this project
            can_view = False
            
            # UESO, Director, VP can see everything
            if request.user.is_authenticated and hasattr(request.user, 'role'):
                if request.user.role in ["UESO", "DIRECTOR", "VP"]:
                    can_view = True
                # Project leader or provider can see their own projects
                elif project.project_leader == request.user or request.user in project.providers.all():
                    can_view = True
                # Dean, Coordinator, Program Head can see all projects from their college
                elif request.user.role in ["DEAN", "COORDINATOR", "PROGRAM_HEAD"]:
                    if request.user.college and project.project_leader.college == request.user.college:
                        can_view = True
            
            # Non-authenticated or other users can only see COMPLETED projects
            if not can_view and project.status == 'COMPLETED':
                can_view = True
            
            if not can_view:
                from django.shortcuts import render
                return render(request, 'users/403_project_visibility.html', status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper