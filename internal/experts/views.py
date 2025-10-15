from django.shortcuts import render
from system.users.decorators import role_required

from system.users.decorators import user_confirmed

@user_confirmed
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"])
def experts_view(request):
    return render(request, 'experts/experts.html')

@user_confirmed
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"])
def expert_profile_view(request):
    return render(request, 'experts/experts_profile.html') # Add Expert Context Later