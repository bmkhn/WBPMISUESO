from django.shortcuts import redirect, get_object_or_404
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
            if require_confirmed:
                # If it's a non-user, just pass through
                if hasattr(request.user, 'is_confirmed') and not request.user.is_confirmed:
                    return redirect('not_confirmed')
            if request.user.role not in allowed_roles:
                return redirect('no_permission')
            return view_func(request, *args, **kwargs)
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
                return HttpResponseForbidden("You do not have permission to view this project.")
        
        return view_func(request, *args, **kwargs)
    return wrapper