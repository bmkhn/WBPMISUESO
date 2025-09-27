from django.shortcuts import get_object_or_404, render
from system.users.decorators import role_required
from django.contrib.auth.decorators import login_required
from system.users.models import College, User
from internal.agenda.models import Agenda
from .models import SustainableDevelopmentGoal, Project
from django.contrib.auth import get_user_model
from .forms import ProjectForm

User = get_user_model()

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
    return render(request, 'projects/user_project.html')


def superuser_project(request):
    return render(request, 'projects/superuser_project.html')


@login_required
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"])
def admin_projects(request):
    # Filters
    sort_by = request.GET.get('sort_by', 'last_updated')
    order = request.GET.get('order', 'desc')
    college = request.GET.get('college', '')
    campus = request.GET.get('campus', '')
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
    years = [d.year for d in projects.dates('start_date', 'year')]

    # Pagination (optional, mimic old logic if needed)
    from django.core.paginator import Paginator
    paginator = Paginator(projects, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(page_obj.number)

    return render(request, 'projects/admin_project.html', {
        'projects': page_obj,
        'colleges': colleges,
        'campuses': campuses,
        'status_choices': status_choices,
        'years': years,
        'sort_by': sort_by,
        'order': order,
        'college': college,
        'campus': campus,
        'status': status,
        'year': year,
        'quarter': quarter,
        'date': date,
        'search': search,
        'page_obj': page_obj,
        'paginator': paginator,
        'page_range': page_range,
        'querystring': request.GET.urlencode().replace('&page='+str(page_obj.number), '') if page_obj else '',
    })


########################################################################################################################

def projects_profile_dispatcher(request, pk):
    user = request.user
    if hasattr(user, 'role'):
        role = user.role
        if role in ["UESO", "DIRECTOR", "VP"]:
            return admin_project_profile(request, pk)
        elif role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
            return superuser_project_profile(request, pk)
        else:
            return user_project_profile(request, pk)
    return user_project_profile(request, pk)


def user_project_profile(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'projects/user_project_profile.html', {'project': project})


def superuser_project_profile(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'projects/superuser_project_profile.html', {'project': project})


@login_required
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"])
def admin_project_profile(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'projects/admin_project_profile.html', {'project': project})


########################################################################################################################


@login_required
@role_required(allowed_roles=["VP", "DIRECTOR"])
def add_project_view(request):
    error = None
    faculty_users = User.objects.filter(role=User.Role.FACULTY)
    provider_users = User.objects.filter(role__in=[User.Role.FACULTY, User.Role.IMPLEMENTER])
    agendas = Agenda.objects.all()
    sdgs = SustainableDevelopmentGoal.objects.all()
    colleges = College.objects.all()
    campus_choices = User.Campus.choices

    logistics_type = 'BOTH'
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                project = form.save(commit=False)
                project.created_by = request.user
                project.status = 'NOT_STARTED'
                project.logistics_type = form.cleaned_data['logistics_type']
                logistics_type = form.cleaned_data['logistics_type']

                project.save()

                # Set many-to-many fields explicitly from POST (hidden inputs)
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

                # Save additional documents robustly
                from .models import ProjectDocument
                files = request.FILES.getlist('additional_documents')
                for f in files:
                    doc = ProjectDocument.objects.create(file=f)
                    project.additional_documents.add(doc)

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