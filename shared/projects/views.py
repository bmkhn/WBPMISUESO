from django.shortcuts import render
from system.users.decorators import role_required
from django.contrib.auth.decorators import login_required
from system.users.models import College, User
from internal.agenda.models import Agenda
from .models import SustainableDevelopmentGoal, Project
from django.contrib.auth import get_user_model
from .forms import ProjectForm

def projects_dispatcher(request):
    user = request.user
    if hasattr(user, 'role'):
        role = user.role
        if role in ["UESO", "DIRECTOR", "VP"]:
            return admin_projects(request)
        elif role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
            return superuser_project(request)
        else:
            return user_projects(request)
    return user_projects(request)

def user_projects(request):
    return render(request, 'projects/user_projects.html')

def superuser_project(request):
    return render(request, 'projects/superuser_projects.html')

def admin_projects(request):
    return render(request, 'projects/admin_projects.html')


User = get_user_model()

@login_required
@role_required(allowed_roles=["VP", "DIRECTOR"])
def add_project_view(request):
    error = None
    users = User.objects.all()
    agendas = Agenda.objects.all()
    sdgs = SustainableDevelopmentGoal.objects.all()
    colleges = College.objects.all()
    campus_choices = User.Campus.choices

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                project = form.save(commit=False)
                project.created_by = request.user
                project.logistics_type = form.cleaned_data['logistics_type']


                project.save()
                form.save_m2m()

                if project.logistics_type == 'BOTH':
                    project.internal_budget = form.cleaned_data['internal_budget']
                    project.external_budget = form.cleaned_data['external_budget']
                    project.sponsor_name = form.cleaned_data['sponsor_name']
                elif project.logistics_type == 'INTERNAL':
                    project.internal_budget = form.cleaned_data['internal_budget']
                    project.external_budget = 0
                    project.sponsor_name = ''
                elif project.logistics_type == 'EXTERNAL':
                    project.internal_budget = 0
                    project.external_budget = form.cleaned_data['external_budget']
                    project.sponsor_name = form.cleaned_data['sponsor_name']

                files = request.FILES.getlist('additional_documents')
                for f in files:
                    project.additional_documents.create(file=f)


                return projects_dispatcher(request)
            except Exception as e:
                error = str(e)
        else:
            error = "Please correct the errors below."
    else:
        form = ProjectForm()
    return render(request, 'projects/add_project.html', {
        'form': form,
        'error': error,
        'users': users,
        'agendas': agendas,
        'sdgs': sdgs,
        'colleges': colleges,
        'campus_choices': campus_choices,
    })