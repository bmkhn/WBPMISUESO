from django.shortcuts import render
from system.users.decorators import role_required

@role_required(allowed_roles=["VP", "DIRECTOR"])
def agenda_view(request):
    return render(request, 'agenda/agenda.html')