from django.shortcuts import render
from system.users.decorators import role_required
from system.users.decorators import user_confirmed

@user_confirmed
@role_required(allowed_roles=["DIRECTOR", "VP", "UESO"])
def goal_view(request):
    return render(request, 'goals/goals.html')
