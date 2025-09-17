from django.shortcuts import render
from system.users.decorators import role_required
from django.contrib.auth.decorators import login_required

@login_required
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"])
def dashboard_view(request):
    user_role = getattr(request.user, 'role', None)
    vpde_content = user_role in ["VP", "DIRECTOR"]
    return render(request, 'dashboard/dashboard.html', {'user_role': user_role, 'vpde_content': vpde_content})