from django.shortcuts import get_object_or_404, render, redirect
from shared import request
from system.users.decorators import role_required
from .models import SustainableDevelopmentGoal, Project, ProjectEvaluation, ProjectEvent
from internal.submissions.models import Submission
from system.users.models import College, User
from internal.agenda.models import Agenda
from .forms import ProjectForm, ProjectEventForm
from django.core.paginator import Paginator
import os
from django.db import models


def get_role_constants():
    ADMIN_ROLES = ["VP", "DIRECTOR", "UESO"]
    SUPERUSER_ROLES = ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]
    FACULTY_ROLE = ["FACULTY", "IMPLEMENTER"]
    COORDINATOR_ROLE = ["COORDINATOR"]
    return ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE

def get_templates(request):
    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"
    return base_template

def project_profile(request, pk):
    return redirect(project_overview, pk=pk)


def project_overview(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()

    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"

    project = get_object_or_404(Project, pk=pk)
    all_sdgs = SustainableDevelopmentGoal.objects.all()
    agendas = Agenda.objects.all()

    if request.method == 'POST' and request.user.role in ADMIN_ROLES:
        # Update project fields from form
        project.title = request.POST.get('title', project.title)
        project.start_date = request.POST.get('start_date', project.start_date)
        project.estimated_end_date = request.POST.get('estimated_end_date', project.estimated_end_date)
        agenda_id = request.POST.get('agenda')
        if agenda_id:
            try:
                project.agenda = Agenda.objects.get(pk=agenda_id)
            except Agenda.DoesNotExist:
                pass
        project.project_type = request.POST.get('project_type', project.project_type)
        project.primary_beneficiary = request.POST.get('primary_beneficiary', project.primary_beneficiary)
        project.estimated_events = request.POST.get('estimated_events', project.estimated_events)
        project.primary_location = request.POST.get('primary_location', project.primary_location)
        project.estimated_trainees = request.POST.get('estimated_trainees', project.estimated_trainees)
        # SDGs (many-to-many)
        sdg_ids = request.POST.getlist('sdgs[]')
        if sdg_ids is not None:
            project.sdgs.set(sdg_ids)
        project.save()
        # Optionally redirect to avoid resubmission
        return redirect(request.path)

    return render(request, 'projects/project_overview.html', {
        'project': project,
        'base_template': base_template,
        "ADMIN_ROLES": ADMIN_ROLES,
        "SUPERUSER_ROLES": SUPERUSER_ROLES,
        "FACULTY_ROLE": FACULTY_ROLE,
        'all_sdgs': all_sdgs,
        'agendas': agendas,
    })


def project_providers(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()
    project = get_object_or_404(Project, pk=pk)
    providers_qs = project.providers.all()

    # Handle add provider POST
    if request.method == 'POST' and request.user.role in ADMIN_ROLES:
        provider_id = request.POST.get('provider_id')
        if provider_id:
            from system.users.models import User
            try:
                provider = User.objects.get(pk=provider_id)
                if provider not in providers_qs:
                    project.providers.add(provider)
                    project.save()
            except User.DoesNotExist:
                pass
        return redirect(request.path)

    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"

    # Candidates: all confirmed faculty/implementers not already providers and not the project leader
    from system.users.models import User
    exclude_ids = list(providers_qs.values_list('id', flat=True))
    if hasattr(project, 'leader') and project.leader:
        exclude_ids.append(project.leader.id)
    provider_candidates = User.objects.filter(
        is_confirmed=True,
        role__in=[User.Role.FACULTY, User.Role.IMPLEMENTER]
    ).exclude(id__in=exclude_ids)

    # Pagination
    paginator = Paginator(providers_qs, 3)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    current = page_obj.number
    total = paginator.num_pages
    if total <= 5:
        page_range = range(1, total + 1)
    elif current <= 3:
        page_range = range(1, 6)
    elif current >= total - 2:
        page_range = range(total - 4, total + 1)
    else:
        page_range = range(current - 2, current + 3)

    return render(request, 'projects/project_providers.html', {
        'project': project,
        'base_template': base_template,
        "ADMIN_ROLES": ADMIN_ROLES,
        "SUPERUSER_ROLES": SUPERUSER_ROLES,
        "FACULTY_ROLE": FACULTY_ROLE,
        'providers': page_obj,
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
        'page_range': page_range,
        'provider_candidates': provider_candidates,
    })


def project_events(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()

    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"

    project = get_object_or_404(Project, pk=pk)
    events = project.events.all().order_by('datetime')
    total = project.estimated_events
    completed = project.event_progress
    percent = int((completed / total) * 100) if total else 0

    event_form = None
    event_to_edit = None
    if request.method == 'POST':
        if request.POST.get('add_event'):
            # Add Event button: create new ProjectEvent and increment estimated_events
            from .models import ProjectEvent
            now = timezone.now()
            new_event = ProjectEvent.objects.create(
                project=project,
                title=f"Event {project.events.count() + 1}",
                description="Description Here",
                datetime=now,
                location="",
                created_at=now,
                created_by=request.user,
                updated_at=now,
                updated_by=request.user,
                image=None,
                placeholder=True
            )
            project.estimated_events += 1
            project.save(update_fields=["estimated_events"])
            return redirect(request.path)
        elif request.POST.get('delete_event_id'):
            # Delete event: remove ProjectEvent and decrement estimated_events
            event_id = request.POST.get('delete_event_id')
            from .models import ProjectEvent
            try:
                event_to_delete = ProjectEvent.objects.get(pk=event_id, project=project)
                event_to_delete.delete()
                if project.estimated_events > 0:
                    project.estimated_events -= 1
                    project.save(update_fields=["estimated_events"])
            except ProjectEvent.DoesNotExist:
                pass
            return redirect(request.path)
        else:
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
        'base_template': base_template,
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
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()

    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"

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

    # Pagination
    paginator = Paginator(documents, 4)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    current = page_obj.number
    total = paginator.num_pages
    if total <= 5:
        page_range = range(1, total + 1)
    elif current <= 3:
        page_range = range(1, 6)
    elif current >= total - 2:
        page_range = range(total - 4, total + 1)
    else:
        page_range = range(current - 2, current + 3)

    return render(request, 'projects/project_files.html', {
        'project': project,
        'base_template': base_template,
        'files': files_page_obj,
        'file_types': file_types,
        'sort_by': sort_by,
        'order': order,
        "ADMIN_ROLES": ADMIN_ROLES,
        "SUPERUSER_ROLES": SUPERUSER_ROLES,
        "FACULTY_ROLE": FACULTY_ROLE,

        'documents': page_obj,
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
        'page_range': page_range,
    })


def project_submissions(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()
    from internal.submissions.models import Submission
    from django.utils import timezone
    # Get all submissions for this project
    all_submissions = Submission.objects.filter(project__pk=pk)
    events = ProjectEvent.objects.filter(project__pk=pk).order_by('datetime')

    # Mark overdue submissions
    now = timezone.now()
    for sub in all_submissions:
        if sub.status == "PENDING" and sub.deadline and sub.deadline < now:
            sub.status = "OVERDUE"
            sub.save(update_fields=["status"])

    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"

    project = get_object_or_404(Project, pk=pk)

    # Status filter
    status_filter = request.GET.get('status', '')

    # Filter and order submissions for display
    from django.db.models import Case, When, Value, IntegerField
    # All roles: APPROVED and REJECTED at the bottom
    if user_role in ["COORDINATOR"]:
        submissions = all_submissions.filter(status__in=["SUBMITTED", "REVISION_REQUESTED", "FORWARDED"])
        if status_filter:
            submissions = submissions.filter(status=status_filter)
        submissions = submissions.annotate(
            status_priority=Case(
                When(status="SUBMITTED", then=Value(0)),
                When(status="REVISION_REQUESTED", then=Value(1)),
                When(status="FORWARDED", then=Value(2)),
                When(status="APPROVED", then=Value(99)),
                When(status="REJECTED", then=Value(100)),
                default=Value(3),
                output_field=IntegerField(),
            )
        ).order_by('status_priority', '-created_at')
    elif user_role in ["VP", "DIRECTOR", "UESO"]:
        submissions = all_submissions
        if status_filter:
            submissions = submissions.filter(status=status_filter)
        submissions = submissions.annotate(
            status_priority=Case(
                When(status="FORWARDED", then=Value(0)),
                When(status="APPROVED", then=Value(99)),
                When(status="REJECTED", then=Value(100)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by('status_priority', '-created_at')
    else:
        submissions = all_submissions
        if status_filter:
            submissions = submissions.filter(status=status_filter)
        submissions = submissions.annotate(
            status_priority=Case(
                When(status="APPROVED", then=Value(99)),
                When(status="REJECTED", then=Value(100)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('status_priority', '-created_at')

    # Pass all status choices for filter dropdown
    status_choices = Submission.SUBMISSION_STATUS_CHOICES

    # Submission Logic
    from django.http import HttpResponseBadRequest
    from django.shortcuts import redirect
    from django.contrib import messages

    if request.method == "POST":
        submission = get_object_or_404(Submission, pk=request.POST.get('submission_id'))
        action = request.POST.get('action')
        print("DEBUG:", action, submission.status)

        # Handle Submission Upload
        if action == "submit" and (submission.status == "PENDING" or submission.status == "REVISION_REQUESTED"):
            sub_type = submission.downloadable.submission_type

            if sub_type == "final":
                submission.file = request.FILES.get("final_file")
                submission.for_product_production = bool(request.POST.get("for_product_production"))
                submission.for_research = bool(request.POST.get("for_research"))
                submission.for_extension = bool(request.POST.get("for_extension"))
            
            elif sub_type == "event":
                submission.image_event = request.FILES.get("image_event")
                submission.image_description = request.POST.get("image_description", "")
                submission.num_trained_individuals = request.POST.get("num_trained_individuals", 0)
                submission.event = ProjectEvent.objects.filter(pk=request.POST.get("event")).first()

            else:  # "file"
                submission.file = request.FILES.get("file_file")

            submission.status = "SUBMITTED"
            submission.submitted_at = timezone.now()
            submission.submitted_by = request.user
            submission.save()

            return redirect(request.path_info)

    # Pagination
    paginator = Paginator(submissions, 3)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    current = page_obj.number
    total = paginator.num_pages
    if total <= 5:
        page_range = range(1, total + 1)
    elif current <= 3:
        page_range = range(1, 6)
    elif current >= total - 2:
        page_range = range(total - 4, total + 1)
    else:
        page_range = range(current - 2, current + 3)

    provider_ids = list(project.providers.values_list('id', flat=True))
    context = {
        "project": project,
        "base_template": base_template,
        "submissions": page_obj,
        "events": events,
        "ADMIN_ROLES": ADMIN_ROLES,
        "COORDINATOR_ROLE": COORDINATOR_ROLE,
        "provider_ids": provider_ids,
        "status_choices": status_choices,
        "status_filter": status_filter,

        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
        'page_range': page_range,
    }
    return render(request, "projects/project_submissions.html", context)


def project_submissions_details(request, pk, submission_id):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()
    
    submission = get_object_or_404(Submission, pk=submission_id, project__pk=pk)

    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"

    project = get_object_or_404(Project, pk=pk)

    context = {
        "project": project,
        "base_template": base_template,
        "submission": submission,
        "ADMIN_ROLES": ADMIN_ROLES,
        "COORDINATOR_ROLE": COORDINATOR_ROLE,
        "FACULTY_ROLE": FACULTY_ROLE,
    }
    return render(request, "projects/project_submissions_details.html", context)

@role_required(allowed_roles=["UESO", "VP", "DIRECTOR", "COORDINATOR", "FACULTY", "IMPLEMENTER"])
def admin_submission_action(request, pk, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id, project__pk=pk)
    from django.utils import timezone
    if request.method == 'POST':
        action = request.POST.get('action')
        if submission.status == 'SUBMITTED' and request.user.role in ["FACULTY", "IMPLEMENTER"]:
            if action == 'unsubmit':
                submission.status = 'PENDING'
                submission.submitted_by = None
                submission.submitted_at = None
                submission.updated_by = request.user
                submission.updated_at = timezone.now()
                submission.save()
        elif submission.status == 'SUBMITTED' and request.user.role == "COORDINATOR": 
            if action == 'forward':
                submission.status = 'FORWARDED'
                submission.reviewed_by = request.user
                submission.reviewed_at = timezone.now()
                submission.updated_by = request.user
                submission.updated_at = timezone.now()
                submission.save()
            elif action == 'request_revision':
                submission.status = 'REVISION_REQUESTED'
                submission.reviewed_by = request.user
                submission.reviewed_at = timezone.now()
                submission.reason_for_revision = request.POST.get('reason', '')
                submission.updated_by = request.user
                submission.updated_at = timezone.now()
                submission.save()
        elif submission.status == 'FORWARDED' and request.user.role in ["VP", "DIRECTOR", "UESO"]:
            if action == 'accept':
                submission.status = 'APPROVED'
                submission.authorized_by = request.user
                submission.authorized_at = timezone.now()
                submission.updated_by = request.user
                submission.updated_at = timezone.now()
                submission.save()
            elif action == 'reject':
                submission.status = 'REJECTED'
                submission.authorized_by = request.user
                submission.authorized_at = timezone.now()
                submission.reason_for_rejection = request.POST.get('reason', '')
                submission.updated_by = request.user
                submission.updated_at = timezone.now()
                submission.save()
            
    return redirect('project_submissions_details', pk=pk, submission_id=submission_id)


def project_expenses(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()

    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"

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
        'base_template': base_template,
        'expenses': expenses,
        "ADMIN_ROLES": ADMIN_ROLES,
        "SUPERUSER_ROLES": SUPERUSER_ROLES,
        "FACULTY_ROLE": FACULTY_ROLE
    })

def project_evaluations(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()

    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"

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
        'base_template': base_template,
        'evaluations': evaluations,
        "ADMIN_ROLES": ADMIN_ROLES,
        "SUPERUSER_ROLES": SUPERUSER_ROLES,
        "FACULTY_ROLE": FACULTY_ROLE
    })


########################################################################################################################


from django.views.decorators.http import require_POST
# Mark project as cancelled
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"])
@require_POST
def cancel_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    project.status = 'CANCELLED'
    project.save()
    return redirect(f'/projects/{pk}/overview/')

# Undo cancel
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"])
@require_POST
def undo_cancel_project(request, pk):
    from datetime import date as dtdate
    project = get_object_or_404(Project, pk=pk)
    today = dtdate.today()
    if project.start_date and project.estimated_end_date:
        if project.start_date <= today <= project.estimated_end_date:
            project.status = 'IN_PROGRESS'
        elif today < project.start_date:
            project.status = 'NOT_STARTED'
        else:
            project.status = 'COMPLETED'
    else:
        project.status = 'IN_PROGRESS'
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
            return faculty_project(request)
    return faculty_project(request)


@role_required(allowed_roles=["FACULTY"])
def faculty_project(request):
    user = request.user
    projects = Project.objects.filter(
        models.Q(project_leader=user) | models.Q(providers=user)
    ).distinct().order_by('-updated_at')

    # Pagination
    paginator = Paginator(projects, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    current = page_obj.number
    total = paginator.num_pages
    if total <= 5:
        page_range = range(1, total + 1)
    elif current <= 3:
        page_range = range(1, 6)
    elif current >= total - 2:
        page_range = range(total - 4, total + 1)
    else:
        page_range = range(current - 2, current + 3)

    return render(request, 'projects/faculty_project.html', {
        'projects': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'page_range': page_range,
    })


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


from django.utils import timezone

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

                project.estimated_events = form.cleaned_data.get('estimated_events', 0)
                now = timezone.now()
                for i in range(1, project.estimated_events + 1):
                    from .models import ProjectEvent
                    ProjectEvent.objects.create(
                        project=project,
                        title=f"Event {i}",
                        description="Description Here",
                        datetime=now,
                        status='SCHEDULED',
                        created_at=now,
                        created_by=request.user,
                        updated_at=now,
                        updated_by=request.user,
                        image=None,
                        placeholder=True
                    )
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