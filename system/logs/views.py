from django.shortcuts import render
from system.users.decorators import role_required
from django.contrib.auth.decorators import login_required
from .models import LogEntry

@role_required(allowed_roles=["VP", "DIRECTOR"])
def logs_view(request):
    logs = LogEntry.objects.select_related('user').order_by('-timestamp')
    return render(request, 'logs/logs.html', {'logs': logs})