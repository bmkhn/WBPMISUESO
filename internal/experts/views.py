from django.shortcuts import render
from system.users.decorators import role_required
from django.contrib.auth.decorators import login_required
from system.users.decorators import user_confirmed

@login_required
@user_confirmed
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"])
def experts_view(request):
    return render(request, 'experts/experts.html')

@login_required
@user_confirmed
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"])
def expert_profile_view(request):
    return render(request, 'experts/experts_profile.html') # Add Expert Context Later