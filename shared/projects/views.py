from django.shortcuts import get_object_or_404, render, redirect
from system.users.decorators import role_required
from django.contrib.auth.decorators import login_required
from .models import SustainableDevelopmentGoal, Project, ProjectEvaluation, ProjectEvent
from system.users.models import College, User
from internal.agenda.models import Agenda
from .forms import ProjectForm, ProjectEventForm
from django.core.paginator import Paginator
import os


def get_role_constants():
    ADMIN_ROLES = ["VP", "DIRECTOR", "UESO"]
    SUPERUSER_ROLES = ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]
    FACULTY_ROLE = "FACULTY"
    return ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE


def project_profile(request, pk):
    return redirect('project_overview', pk=pk)


def project_overview(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE = get_role_constants()

    project = get_object_or_404(Project, pk=pk)
    return render(request, 'projects/project_overview.html', {
        'project': project,
        "ADMIN_ROLES": ADMIN_ROLES,
        "SUPERUSER_ROLES": SUPERUSER_ROLES,
        "FACULTY_ROLE": FACULTY_ROLE
    })


def project_providers(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE = get_role_constants()

    project = get_object_or_404(Project, pk=pk)
    return render(request, 'projects/project_providers.html', {
        'project': project,
        "ADMIN_ROLES": ADMIN_ROLES,
        "SUPERUSER_ROLES": SUPERUSER_ROLES,
        "FACULTY_ROLE": FACULTY_ROLE
    })


def project_events(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE = get_role_constants()
    project = get_object_or_404(Project, pk=pk)
    events_qs = project.events.all().order_by('datetime')
    total = project.estimated_events
    events = events_qs[:total] if total else events_qs
    completed = events_qs.filter(status='COMPLETED').count()
    percent = int((completed / total) * 100) if total else 0

    event_form = None
    event_to_edit = None
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        if event_id:
            event_to_edit = get_object_or_404(project.events, pk=event_id)
            # Remove required validation for datetime and image
            post_data = request.POST.copy()
            files_data = request.FILES.copy()
            if not post_data.get('datetime'):
                post_data['datetime'] = event_to_edit.datetime
            if not files_data.get('image'):
                # If no new image uploaded, keep old image
                files_data['image'] = event_to_edit.image
            event_form = ProjectEventForm(post_data, files_data, instance=event_to_edit)
        else:
            event_form = ProjectEventForm(request.POST, request.FILES)
        if event_form.is_valid():
            event = event_form.save(commit=False)
            event.project = project
            event.created_by = request.user
            event.status = 'SCHEDULED'
            event.save()
            return redirect(request.path)

    if not event_form:
        event_form = ProjectEventForm()

    return render(request, 'projects/project_events.html', {
        'project': project,
        'events': events,
        'total': total,
        'completed': completed,
        'percent': percent,
        'event_form': event_form,
        'event_to_edit': event_to_edit,
        "ADMIN_ROLES": ADMIN_ROLES,
        "SUPERUSER_ROLES": SUPERUSER_ROLES,
        "FACULTY_ROLE": FACULTY_ROLE
    })


def project_files(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE = get_role_constants()
    project = get_object_or_404(Project, pk=pk)
    documents = project.documents.all()

    search = request.GET.get('search', '')
    sort_by = request.GET.get('sort_by', 'name')
    order = request.GET.get('order', 'asc')
    file_type = request.GET.get('file_type', '')
    date = request.GET.get('date', '')

    extensions = set(documents.values_list('file', flat=True))
    extensions = set([os.path.splitext(f)[1][1:].lower() for f in extensions if f])

    if file_type:
        documents = [doc for doc in documents if doc.extension == file_type]
    if date:
        documents = [doc for doc in documents if str(doc.uploaded_at.date()) == date]
    if search:
        documents = [doc for doc in documents if search.lower() in doc.name.lower()]
 
    sort_map = {
        'name': lambda x: x.name,
        'file_type': lambda x: x.extension,
        'size': lambda x: x.size,
        'date': lambda x: x.uploaded_at,
    }

    sort_func = sort_map.get(sort_by, lambda x: x.name)
    documents = sorted(documents, key=sort_func, reverse=(order=='desc'))
    files_page_number = int(request.GET.get('files_page', 1))
    files_paginator = Paginator(documents, 4)
    files_page_obj = files_paginator.get_page(files_page_number)
    file_types = sorted(list(extensions))

    return render(request, 'projects/project_files.html', {
        'project': project,
        'files': files_page_obj,
        'file_types': file_types,
        'sort_by': sort_by,
        'order': order,
        "ADMIN_ROLES": ADMIN_ROLES,
        "SUPERUSER_ROLES": SUPERUSER_ROLES,
        "FACULTY_ROLE": FACULTY_ROLE,
    })


def project_submissions(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE = get_role_constants()
    project = get_object_or_404(Project, pk=pk)
    submissions = getattr(project, 'submissions', None)

    if submissions is None and hasattr(project, 'submission_set'):
        submissions = project.submission_set.all()
    elif submissions is None:
        submissions = []
    return render(request, 'projects/project_submissions.html', {
        'project': project, 
        'submissions': submissions,
        "ADMIN_ROLES": ADMIN_ROLES,
        "SUPERUSER_ROLES": SUPERUSER_ROLES,
        "FACULTY_ROLE": FACULTY_ROLE,
    })


def project_expenses(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE = get_role_constants()
    project = get_object_or_404(Project, pk=pk)

    expenses = [
        {
            'title': 'Venue Rental',
            'reason': 'Rented hall for event',
            'amount': 5000.00,
            'date': '2025-09-20',
            'receipt': 'https://via.placeholder.com/120x120.png?text=Receipt',
        },
        {
            'title': 'Food & Catering',
            'reason': 'Lunch for participants',
            'amount': 3200.50,
            'date': '2025-09-21',
            'receipt': '',
        },
        {
            'title': 'Materials',
            'reason': 'Printed handouts and supplies',
            'amount': 1500.75,
            'date': '2025-09-22',
            'receipt': 'https://via.placeholder.com/120x120.png?text=Receipt',
        },
    ]
    return render(request, 'projects/project_expenses.html', {
        'project': project, 
        'expenses': expenses,
        "ADMIN_ROLES": ADMIN_ROLES,
        "SUPERUSER_ROLES": SUPERUSER_ROLES,
        "FACULTY_ROLE": FACULTY_ROLE
    })

def project_evaluations(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE = get_role_constants()
    project = get_object_or_404(Project, pk=pk)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        evaluated_by = request.user
        if rating and evaluated_by:
            ProjectEvaluation.objects.create(
                project=project,
                evaluated_by=evaluated_by,
                comment=comment,
                rating=int(rating)
            )
        return redirect(request.path)
    evaluations = project.evaluations.select_related('evaluated_by').order_by('-created_at')
    return render(request, 'projects/project_evaluations.html', {
        'project': project, 
        'evaluations': evaluations,
        "ADMIN_ROLES": ADMIN_ROLES,
        "SUPERUSER_ROLES": SUPERUSER_ROLES,
        "FACULTY_ROLE": FACULTY_ROLE
    })


########################################################################################################################


from django.views.decorators.http import require_POST
# Mark project as cancelled
@login_required
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"])
@require_POST
def cancel_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    project.status = 'CANCELLED'
    project.save()
    return redirect(f'/projects/{pk}/overview/')

# Undo cancel
@login_required
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"])
@require_POST
def undo_cancel_project(request, pk):
    from datetime import date as dtdate
    project = get_object_or_404(Project, pk=pk)
    today = dtdate.today()
    if project.start_date and project.estimated_end_date:
        if project.start_date <= today <= project.estimated_end_date:
            project.status = 'ONGOING'
        elif today < project.start_date:
            project.status = 'NOT_STARTED'
        else:
            project.status = 'COMPLETED'
    else:
        project.status = 'ONGOING'
    project.save()
    return redirect(f'/projects/{pk}/overview/')


########################################################################################################################


def projects_dispatcher(request):
    user = request.user
    if hasattr(user, 'role'):
        role = user.role
        if role in ["UESO", "DIRECTOR", "VP", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
            return admin_project(request)
        else:
            return user_projects(request)
    return user_projects(request)


@login_required
@role_required(allowed_roles=["FACULTY"])
def user_projects(request):
    return render(request, 'projects/user_project.html')


@login_required
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"])
def admin_project(request):
    ADMIN_ROLES = ["VP", "DIRECTOR", "UESO"]
    SUPERUSER_ROLES = ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]

    # Filters
    sort_by = request.GET.get('sort_by', 'last_updated')
    order = request.GET.get('order', 'desc')
    college = request.GET.get('college', '')
    campus = request.GET.get('campus', '')
    agenda = request.GET.get('agenda', '')
    status = request.GET.get('status', '')
    year = request.GET.get('year', '')
    quarter = request.GET.get('quarter', '')
    date = request.GET.get('date', '')
    search = request.GET.get('search', '')

    projects = Project.objects.all()

    # Filter by college/campus via team leader
    if college:
        projects = projects.filter(project_leader__college__id=college)
    if campus:
        projects = projects.filter(project_leader__campus=campus)
    if agenda:
        projects = projects.filter(agenda__id=agenda)
    if status:
        projects = projects.filter(status=status)
    if year:
        projects = projects.filter(start_date__year=year)
    if quarter:
        # Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec
        qmap = {'1': (1,3), '2': (4,6), '3': (7,9), '4': (10,12)}
        if quarter in qmap:
            start, end = qmap[quarter]
            projects = projects.filter(start_date__month__gte=start, start_date__month__lte=end)
    if date:
        projects = projects.filter(start_date=date)
    if search:
        projects = projects.filter(title__icontains=search)

    # Sorting
    sort_map = {
        'title': 'title',
        'last_updated': 'updated_at',
        'start_date': 'start_date',
        'progress': '', # Placeholder, not supported in DB sort
    }
    sort_field = sort_map.get(sort_by, 'title')
    if sort_field:
        if order == 'desc':
            sort_field = '-' + sort_field
        projects = projects.order_by(sort_field)
    # If progress sort, sort in Python
    elif sort_by == 'progress':
        projects = sorted(projects, key=lambda p: (p.progress[0] / p.progress[1]) if p.progress[1] else 0, reverse=(order=='desc'))

    # Filter options
    colleges = College.objects.all()
    campuses = User.Campus.choices
    status_choices = Project.STATUS_CHOICES
    agendas = Agenda.objects.all()
    years = [d.year for d in projects.dates('start_date', 'year')]

    # Pagination (optional, mimic old logic if needed)
    paginator = Paginator(projects, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(page_obj.number)

    return render(request, 'projects/admin_project.html', {
        'projects': page_obj,
        'colleges': colleges,
        'campuses': campuses,
        'status_choices': status_choices,
        'agendas': agendas,
        'years': years,
        'sort_by': sort_by,
        'order': order,
        'college': college,
        'campus': campus,
        'agenda': agenda,
        'status': status,
        'year': year,
        'quarter': quarter,
        'date': date,
        'search': search,
        'page_obj': page_obj,
        'paginator': paginator,
        'page_range': page_range,
        'querystring': request.GET.urlencode().replace('&page='+str(page_obj.number), '') if page_obj else '',
        "ADMIN_ROLES": ADMIN_ROLES,
        "SUPERUSER_ROLES": SUPERUSER_ROLES,
    })


########################################################################################################################


@login_required
@role_required(allowed_roles=["VP", "DIRECTOR"])
def add_project_view(request):
    error = None
    faculty_users = User.objects.filter(role=User.Role.FACULTY, is_confirmed=True)
    provider_users = User.objects.filter(role__in=[User.Role.FACULTY, User.Role.IMPLEMENTER], is_confirmed=True)
    agendas = Agenda.objects.all()
    sdgs = SustainableDevelopmentGoal.objects.all()
    colleges = College.objects.all()
    campus_choices = User.Campus.choices

    logistics_type = 'BOTH'
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Save project (basic fields)
                project = form.save(commit=False)
                project.created_by = request.user
                project.status = 'NOT_STARTED'
                project.logistics_type = form.cleaned_data['logistics_type']
                logistics_type = form.cleaned_data['logistics_type']
                project.save()

                # Set many-to-many fields
                provider_ids = request.POST.getlist('providers[]')
                if provider_ids:
                    project.providers.set(provider_ids)
                else:
                    providers = form.cleaned_data.get('providers')
                    if providers:
                        project.providers.set(providers)

                sdg_ids = request.POST.getlist('sdgs[]')
                if sdg_ids:
                    project.sdgs.set(sdg_ids)
                else:
                    sdgs = form.cleaned_data.get('sdgs')
                    if sdgs:
                        project.sdgs.set(sdgs)

                # Set logistics fields
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
                project.save()

                # Handle proposal document
                proposal_file = request.FILES.get('proposal_document')
                if proposal_file:
                    from .models import ProjectDocument
                    proposal_doc = ProjectDocument.objects.create(
                        project=project,
                        file=proposal_file,
                        document_type='PROPOSAL'
                    )
                    project.proposal_document = proposal_doc
                    project.save()

                # Handle additional documents
                additional_files = request.FILES.getlist('additional_documents')
                for add_file in additional_files:
                    from .models import ProjectDocument
                    add_doc = ProjectDocument.objects.create(
                        project=project,
                        file=add_file,
                        document_type='ADDITIONAL'
                    )
                    project.additional_documents.add(add_doc)
                project.save()

                return render(request, 'projects/add_project.html', {
                    'form': ProjectForm(),
                    'success': True,
                    'error': error,
                    'faculty_users': faculty_users,
                    'provider_users': provider_users,
                    'agendas': agendas,
                    'sdgs': sdgs,
                    'colleges': colleges,
                    'campus_choices': campus_choices,
                    'logistics_type': logistics_type,
                })
            except Exception as e:
                error = str(e)
        else:
            error = "Please correct the errors below."
        logistics_type = request.POST.get('logistics_type', 'BOTH')
    else:
        form = ProjectForm()
    return render(request, 'projects/add_project.html', {
        'form': form,
        'error': error,
        'faculty_users': faculty_users,
        'provider_users': provider_users,
        'agendas': agendas,
        'sdgs': sdgs,
        'colleges': colleges,
        'campus_choices': campus_choices,
        'logistics_type': logistics_type,
    })
