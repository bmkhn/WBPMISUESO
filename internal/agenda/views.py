
from .forms import AgendaForm
from .models import Agenda
from system.users.decorators import role_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from shared.projects.models import Project


# Agenda View
@role_required(allowed_roles=["VP", "DIRECTOR"], require_confirmed=True)
def agenda_view(request):
    agendas = Agenda.objects.prefetch_related('concerned_colleges', 'projects').all()
    # Use the related_name 'projects' to get all projects for each agenda
    agenda_projects = {agenda.id: agenda.projects.all() for agenda in agendas}
    return render(request, 'agenda/agenda.html', {
        'agendas': agendas,
        'agenda_projects': agenda_projects,
    })


# Add Agenda View
@role_required(allowed_roles=["VP", "DIRECTOR"], require_confirmed=True)
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


# Edit Agenda View
@role_required(allowed_roles=["VP", "DIRECTOR"], require_confirmed=True)
def edit_agenda_view(request, agenda_id):
    try:
        agenda = Agenda.objects.get(id=agenda_id)
    except Agenda.DoesNotExist:
        return render(request, 'agenda/edit_agenda.html', {'error': 'Agenda not found.'})

    if request.method == 'POST':
        form = AgendaForm(request.POST, instance=agenda)
        if form.is_valid():
            form.save()
            selected_college_ids = [str(c.id) for c in form.cleaned_data['concerned_colleges']]
            return render(request, 'agenda/edit_agenda.html', {
                'form': form,
                'success': True,
                'selected_college_ids': selected_college_ids if selected_college_ids else [],
            })
        else:
            selected_college_ids = request.POST.getlist('concerned_colleges')
    else:
        form = AgendaForm(instance=agenda)
        selected_college_ids = [str(c.id) for c in agenda.concerned_colleges.all()] if agenda else []
    return render(request, 'agenda/edit_agenda.html', {
        'form': form,
        'selected_college_ids': selected_college_ids if selected_college_ids else [],
    })



# Delete Agenda View
@role_required(allowed_roles=["VP", "DIRECTOR"], require_confirmed=True)
def delete_agenda_view(request, agenda_id):
    agenda = Agenda.objects.get(id=agenda_id)
    agenda.delete()
    return HttpResponseRedirect(reverse('agenda'))