from django.shortcuts import render
from system.users.decorators import role_required


@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "DEAN", "PROGRAM_HEAD", "COORDINATOR"], require_confirmed=True)
def analytics_view(request):
    return render(request, 'analytics/analytics.html')