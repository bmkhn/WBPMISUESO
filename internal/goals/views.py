from django.shortcuts import render
from system.users.decorators import role_required

@role_required(allowed_roles=["DIRECTOR", "VP", "UESO"])
def goal_view(request):
    return render(request, 'goals/goals.html')
