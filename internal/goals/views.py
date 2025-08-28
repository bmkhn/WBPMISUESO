from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from system.users.decorators import role_required

@login_required
@role_required(allowed_roles=["DIRECTOR", "VP", "UESO"])
def goal_view(request):
    return render(request, 'goals/goals.html')
