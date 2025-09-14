from .forms import AgendaForm
from .models import Agenda
from system.users.decorators import role_required
from django.contrib.auth.decorators import login_required


# Agenda View
@login_required
@role_required(allowed_roles=["VP", "DIRECTOR"])
def agenda_view(request):
    agendas = Agenda.objects.prefetch_related('concerned_colleges').all()
    return render(request, 'agenda/agenda.html', {'agendas': agendas})


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


# Edit Agenda View
@login_required
@role_required(allowed_roles=["VP", "DIRECTOR"])
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
            # If form is invalid, try to get from POST data
            selected_college_ids = request.POST.getlist('concerned_colleges')
    else:
        form = AgendaForm(instance=agenda)
        selected_college_ids = [str(c.id) for c in agenda.concerned_colleges.all()] if agenda else []
    return render(request, 'agenda/edit_agenda.html', {
        'form': form,
        'selected_college_ids': selected_college_ids if selected_college_ids else [],
    })



# Delete Agenda View
@login_required
@role_required(allowed_roles=["VP", "DIRECTOR"])
def delete_agenda_view(request, agenda_id):
    try:
        agenda = Agenda.objects.get(id=agenda_id)
    except Agenda.DoesNotExist:
        return render(request, 'agenda/agenda.html', {'agendas': Agenda.objects.all(), 'error': 'Agenda not found.'})

    if request.method == 'POST':
        agenda.delete()
        return render(request, 'agenda/agenda.html', {'agendas': Agenda.objects.all(), 'success': 'Agenda deleted successfully.'})
    else:
        # Show confirmation dialog
        return render(request, 'agenda/delete_agenda.html', {'agenda': agenda})