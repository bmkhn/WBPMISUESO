from .forms import AgendaForm
from .models import Agenda
from system.users.decorators import role_required
from django.contrib.auth.decorators import login_required


# Agenda View
@login_required
@role_required(allowed_roles=["VP", "DIRECTOR"])
def agenda_view(request):
    return render(request, 'agenda/agenda.html')


# Add Agenda View
@login_required
@role_required(allowed_roles=["VP", "DIRECTOR"])
def add_agenda_view(request):
    if request.method == 'POST':
        form = AgendaForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'agenda/add_agenda.html', {'form': AgendaForm(), 'success': True})
    else:
        form = AgendaForm()
    return render(request, 'agenda/add_agenda.html', {'form': form})
from django.shortcuts import render