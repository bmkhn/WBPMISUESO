from django.shortcuts import get_object_or_404, render, redirect
from internal.submissions.views import delete_submission
from shared import request
from system.logs.models import LogEntry
from system.notifications.models import Notification
from system.users.decorators import role_required, project_visibility_required
from .models import SustainableDevelopmentGoal, Project, ProjectEvaluation, ProjectEvent, ProjectUpdate, ProjectExpense
from internal.goals.models import Goal
from internal.submissions.models import Submission
from system.users.models import College, User, Campus
from internal.agenda.models import Agenda
from .forms import ProjectForm, ProjectEventForm
from django.core.paginator import Paginator
import os
from django.db import models
from django.db.models import Q, BooleanField, ExpressionWrapper, Sum # Added Sum
from decimal import Decimal # Added Decimal
from django.contrib import messages # Added messages
from django.utils import timezone # Added timezone for use in related functions
from django.http import HttpResponseRedirect, JsonResponse # Added for related functions
from django.urls import reverse # Added for related functions
from datetime import date as dtdate # Added for related functions
from shared.budget.models import CollegeBudget # Added for budget functions
from datetime import datetime # Added for budget functions


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


@project_visibility_required
def project_profile(request, pk):
    # Check if user is authenticated and has role
    if request.user.is_authenticated and hasattr(request.user, 'role'):
        # Mark project alerts as viewed for faculty users
        if request.user.role in ["FACULTY", "IMPLEMENTER"]:
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            project = get_object_or_404(Project, pk=pk)
            updated = ProjectUpdate.objects.filter(user=request.user, project=project, viewed=False).update(viewed=True)
            if updated and request.method == 'GET' and not request.GET.get('new'):
                url = reverse('project_profile', args=[pk])
                params = request.GET.copy()
                params['new'] = '1'
                url += '?' + params.urlencode()
                return HttpResponseRedirect(url)
    else:
        # Non-authenticated users can only view completed projects
        project = get_object_or_404(Project, pk=pk, status='COMPLETED')
    
    return redirect(project_overview, pk=pk)


@project_visibility_required
def project_overview(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()

    # Determine base template and access control
    user_role = getattr(request.user, 'role', None) if request.user.is_authenticated else None
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
        # Authenticated users with roles can see all projects
        project = get_object_or_404(Project, pk=pk)
    else:
        base_template = "base_public.html"
        # Non-authenticated users or users without admin roles can only see completed projects
        if not request.user.is_authenticated:
            project = get_object_or_404(Project, pk=pk, status='COMPLETED')
        else:
            project = get_object_or_404(Project, pk=pk)

    all_sdgs = SustainableDevelopmentGoal.objects.all()
    agendas = Agenda.objects.all()

    if request.method == 'POST' and user_role in ADMIN_ROLES:
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


@project_visibility_required
def project_providers(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()
    
    # Determine base template and access control
    user_role = getattr(request.user, 'role', None) if request.user.is_authenticated else None
    
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
        # Authenticated users with roles can see all projects
        project = get_object_or_404(Project, pk=pk)
    else:
        base_template = "base_public.html"
        # Non-authenticated users or users without admin roles can only see completed projects
        if not request.user.is_authenticated:
            project = get_object_or_404(Project, pk=pk, status='COMPLETED')
        else:
            project = get_object_or_404(Project, pk=pk)
    
    providers_qs = project.providers.all()

    # Handle add provider POST
    if request.method == 'POST' and user_role in ADMIN_ROLES:
        provider_id = request.POST.get('provider_id')
        if provider_id:
            from system.users.models import User
            try:
                provider = User.objects.get(pk=provider_id)
                if provider not in providers_qs:
                    project.providers.add(provider)
                    project.save()
                    
                    # Create alert for the newly added provider
                    from .models import ProjectUpdate
                    # Need to import timezone for ProjectUpdate creation
                    
                    ProjectUpdate.objects.create(
                        user=provider,
                        project=project,
                        submission=None,  # No submission for provider addition alerts
                        status='PROJECT_ASSIGNED',
                        viewed=False,
                        updated_at=timezone.now()
                    )
            except User.DoesNotExist:
                pass
        return redirect(request.path)

    # Candidates: all confirmed users except CLIENT, not already providers and not the project leader
    from system.users.models import User
    exclude_ids = list(providers_qs.values_list('id', flat=True))
    if hasattr(project, 'leader') and project.leader:
        exclude_ids.append(project.leader.id)
    provider_candidates = User.objects.filter(
        is_confirmed=True
    ).exclude(role=User.Role.CLIENT).exclude(id__in=exclude_ids)

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


@project_visibility_required
def project_events(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()

    # Determine base template and access control
    user_role = getattr(request.user, 'role', None) if request.user.is_authenticated else None
    
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
        # Authenticated users with roles can see all projects
        project = get_object_or_404(Project, pk=pk)
    else:
        base_template = "base_public.html"
        # Non-authenticated users or users without admin roles can only see completed projects
        if not request.user.is_authenticated:
            project = get_object_or_404(Project, pk=pk, status='COMPLETED')
        else:
            project = get_object_or_404(Project, pk=pk)

    # Order events: those with datetime=None at the bottom
    from django.db.models import F, Value, BooleanField, ExpressionWrapper
    from internal.submissions.models import Submission
    
    events = project.events.annotate(
        has_datetime=ExpressionWrapper(Q(datetime__isnull=False), output_field=BooleanField())
    ).order_by('-has_datetime', 'datetime')
    
    # Add submission status information to events
    for event in events:
        event.related_submissions = Submission.objects.filter(event=event).first()
    
    total = project.estimated_events
    completed = project.event_progress
    percent = int((completed / total) * 100) if total else 0

    event_form = None
    event_to_edit = None
    if request.method == 'POST':
        if request.POST.get('add_event'):
            # Add Activity: create new ProjectEvent with modal data (does NOT change estimated_events)
            from .models import ProjectEvent
            # timezone is imported at the top
            now = timezone.now()
            
            # Get data from modal form (note: modal uses 'add_event_' prefix for field names)
            title = request.POST.get('add_event_title', f"Event {project.events.count() + 1}")
            description = request.POST.get('add_event_description', '')  # Optional description field
            datetime_str = request.POST.get('add_event_datetime', None)
            location = request.POST.get('add_event_location', '')
            
            # Determine if this is a placeholder based on whether datetime and location are provided
            is_placeholder = not (datetime_str and location)
            
            ProjectEvent.objects.create(
                project=project,
                title=title,
                description=description,
                datetime=datetime_str if datetime_str else None,
                location=location,
                created_at=now,
                created_by=request.user,
                updated_at=now,
                updated_by=request.user,
                image=None,
                placeholder=is_placeholder
            )
            # Do NOT increment estimated_events - it's set separately and represents planned activities
            return redirect(request.path)
        elif request.POST.get('delete_event_id'):
            # Delete event: remove ProjectEvent (does NOT change estimated_events)
            event_id = request.POST.get('delete_event_id')
            from .models import ProjectEvent
            from internal.submissions.models import Submission
            try:
                event_to_delete = ProjectEvent.objects.get(pk=event_id, project=project)
                
                # Check for ALL submissions related to this event (not just approved ones)
                related_submissions = Submission.objects.filter(event=event_to_delete)
                
                # Check if this event has approved submissions and adjust counters
                approved_submission = related_submissions.filter(status='APPROVED').first()
                
                if approved_submission:
                    # Decrement event progress if this was a completed event
                    if project.event_progress > 0:
                        project.event_progress -= 1
                    
                    # Subtract trained individuals if this event contributed to the total
                    if approved_submission.num_trained_individuals:
                        trained_count = approved_submission.num_trained_individuals
                        if project.total_trained_individuals >= trained_count:
                            project.total_trained_individuals -= trained_count
                
                # Delete all related submissions for this event
                related_submissions.delete()
                
                # Delete the event itself
                event_to_delete.delete()
                
                # Do NOT decrement estimated_events - it represents planned activities, not actual count
                project.save(update_fields=["event_progress", "total_trained_individuals"])
                    
            except ProjectEvent.DoesNotExist:
                pass
            return redirect(request.path)
        else:
            event_id = request.POST.get('event_id')
            if event_id:
                # Edit existing event
                event_to_edit = get_object_or_404(project.events, pk=event_id, project=project)
                event_to_edit.title = request.POST.get('title', event_to_edit.title)
                event_to_edit.description = request.POST.get('description', event_to_edit.description)
                event_to_edit.datetime = request.POST.get('datetime', event_to_edit.datetime)
                event_to_edit.location = request.POST.get('location', event_to_edit.location)
                
                if event_to_edit.datetime and event_to_edit.location:
                    event_to_edit.placeholder = False
                event_to_edit.updated_by = request.user
                event_to_edit.updated_at = timezone.now()

                event_to_edit.save()
                return redirect(request.path)  # Add redirect to refresh page
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


@project_visibility_required
def project_files(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()

    # Determine base template and access control
    user_role = getattr(request.user, 'role', None) if request.user.is_authenticated else None
    
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
        # Authenticated users with roles can see all projects
        project = get_object_or_404(Project, pk=pk)
    else:
        base_template = "base_public.html"
        # Non-authenticated users or users without admin roles can only see completed projects
        if not request.user.is_authenticated:
            project = get_object_or_404(Project, pk=pk, status='COMPLETED')
        else:
            project = get_object_or_404(Project, pk=pk)
    
    documents = project.documents.all()
    

    search = request.GET.get('search', '')
    sort_by = request.GET.get('sort_by', 'name')
    order = request.GET.get('order', 'asc')
    file_type = request.GET.get('file_type', '')

    extensions = set(documents.values_list('file', flat=True))
    extensions = set([os.path.splitext(f)[1][1:].lower() for f in extensions if f])

    if file_type:
        documents = [doc for doc in documents if doc.extension == file_type]
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


@project_visibility_required
def project_submissions(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()
    from internal.submissions.models import Submission
    # timezone is imported at the top
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
    # messages is imported at the top

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
        "SUPERUSER_ROLES": SUPERUSER_ROLES,
        "COORDINATOR_ROLE": COORDINATOR_ROLE,
        "FACULTY_ROLE": FACULTY_ROLE,
        "provider_ids": provider_ids,
        "status_choices": status_choices,
        "status_filter": status_filter,

        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
        'page_range': page_range,
        'now': now,
    }
    return render(request, "projects/project_submissions.html", context)


@project_visibility_required
def project_submissions_details(request, pk, submission_id):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()
    
    submission = get_object_or_404(Submission, pk=submission_id, project__pk=pk)

    # Mark submission alerts as viewed for faculty users
    if request.user.role in ["FACULTY", "IMPLEMENTER"]:
        # imports are at the top
        updated = ProjectUpdate.objects.filter(
            user=request.user, 
            project__pk=pk, 
            submission=submission, 
            viewed=False
        ).update(viewed=True)
        if updated and request.method == 'GET' and not request.GET.get('new'):
            url = reverse('project_submissions_details', args=[pk, submission_id])
            params = request.GET.copy()
            params['new'] = '1'
            url += '?' + params.urlencode()
            return HttpResponseRedirect(url)

    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"

    project = get_object_or_404(Project, pk=pk)
    events = ProjectEvent.objects.filter(project__pk=pk).order_by('datetime')

    # Handle submission POST requests
    if request.method == "POST":
        # timezone is imported at the top
        action = request.POST.get('action')
        
        # Handle Submission Upload (allow PENDING, REVISION_REQUESTED, REJECTED, and OVERDUE)
        if action == "submit" and submission.status in ["PENDING", "REVISION_REQUESTED", "REJECTED", "OVERDUE"]:
            sub_type = submission.downloadable.submission_type

            if sub_type == "final":
                submission.file = request.FILES.get("final_file")
                submission.for_product_production = bool(request.POST.get("for_product_production"))
                submission.for_research = bool(request.POST.get("for_research"))
                submission.for_extension = bool(request.POST.get("for_extension"))
            
            elif sub_type == "event":
                # For event submissions, the event is already linked via submission.event
                if submission.event:
                    # Update the ProjectEvent with image and description
                    submission.event.image = request.FILES.get("image_event")
                    submission.event.description = request.POST.get("image_description", "")
                    submission.event.save()
                    
                    # Update the project's total trained individuals
                    num_trained = int(request.POST.get("num_trained_individuals", 0))
                    project.total_trained_individuals += num_trained
                    project.save()
                
                # Keep the submission fields for backward compatibility 
                submission.image_event = request.FILES.get("image_event")
                submission.image_description = request.POST.get("image_description", "")
                submission.num_trained_individuals = request.POST.get("num_trained_individuals", 0)

            else:  # "file"
                submission.file = request.FILES.get("file_file")

            # Check if submission is late
            now = timezone.now()
            if submission.deadline and now > submission.deadline:
                submission.is_late_submission = True
            
            submission.status = "SUBMITTED"
            submission.submitted_at = now
            submission.submitted_by = request.user
            submission.updated_by = request.user
            submission.updated_at = now
            submission.save()

            from urllib.parse import quote
            submission_title = submission.downloadable.name if submission.downloadable else "Submission"
            return redirect(f'/projects/{pk}/submission/?success=true&action=submit&title={quote(submission_title)}')

    provider_ids = list(project.providers.values_list('id', flat=True))
    
    # Check if project leader has no college (determines if COORDINATOR review is needed)
    project_leader_has_no_college = project.project_leader and not project.project_leader.college
    
    # Check if current user is NOT involved in the project (for admin review buttons)
    user_not_in_project = (
        request.user.id != project.project_leader.id and 
        request.user.id not in provider_ids
    )
    
    context = {
        "project": project,
        "base_template": base_template,
        "submission": submission,
        "events": events,
        "provider_ids": provider_ids,
        "project_leader_has_no_college": project_leader_has_no_college,
        "user_not_in_project": user_not_in_project,
        "ADMIN_ROLES": ADMIN_ROLES,
        "COORDINATOR_ROLE": COORDINATOR_ROLE,
        "FACULTY_ROLE": FACULTY_ROLE,
    }
    return render(request, "projects/project_submissions_details.html", context)

# ACTIONS
@role_required(allowed_roles=["UESO", "VP", "DIRECTOR", "COORDINATOR", "FACULTY", "IMPLEMENTER", "DEAN", "PROGRAM_HEAD"], require_confirmed=True)
def admin_submission_action(request, pk, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id, project__pk=pk)
    # timezone is imported at the top
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Check if user is project leader or provider
        is_project_member = (
            request.user.id == submission.project.project_leader.id or 
            submission.project.providers.filter(id=request.user.id).exists()
        )
        
        if submission.status == 'SUBMITTED' and is_project_member:
            if action == 'unsubmit':
                submission.status = 'PENDING'
                submission.submitted_by = None
                submission.submitted_at = None
                submission.file = None
                submission.updated_by = request.user
                submission.updated_at = timezone.now()
                submission.save()
        elif submission.status == 'PENDING' and request.user.role in ["UESO", "VP", "DIRECTOR"]:
            if action == 'delete':
                from system.logs.models import LogEntry
                from system.notifications.models import Notification
                from system.users.models import User
                
                # Store submission data before deletion
                project = submission.project
                project_title = project.title
                form_name = str(submission.downloadable.name_with_ext)
                project_leader = project.project_leader
                project_college = project_leader.college if project_leader else None
                submission_id = submission.id
                
                # Get all people involved for notifications
                notification_recipients = []
                if project_leader:
                    notification_recipients.append(project_leader)
                notification_recipients.extend(list(project.providers.all()))
                
                # Also notify coordinator of the same college
                if project_college:
                    coordinators = User.objects.filter(
                        role='COORDINATOR',
                        college=project_college,
                        is_confirmed=True,
                        is_active=True
                    )
                    notification_recipients.extend(coordinators)
                
                # Notify UESO, Director, VP
                supervisors = User.objects.filter(
                    role__in=['UESO', 'DIRECTOR', 'VP'],
                    is_confirmed=True,
                    is_active=True
                )
                notification_recipients.extend(supervisors)
                
                # Remove duplicates
                notification_recipients = list(set(notification_recipients))
                
                # Create log entry BEFORE deletion
                log_entry = LogEntry.objects.create(
                    user=request.user,
                    action='DELETE',
                    model='Submission',
                    object_id=submission_id,
                    object_repr=f"{form_name} - {project_title}",
                    details=f"Submission requirement '{form_name}' for project '{project_title}' has been deleted by {request.user.get_full_name()}",
                    url='',  # No URL since the submission no longer exists
                    is_notification=False  # We'll create notifications manually
                )
                
                # Create notifications manually for all involved users (except the actor)
                notifications_to_create = [
                    Notification(
                        recipient=recipient,
                        actor=request.user,
                        action='DELETE',
                        model='Submission',
                        object_id=submission_id,
                        object_repr=f"{form_name} - {project_title}",
                        details=f"Submission requirement '{form_name}' for project '{project_title}' has been deleted",
                        url='',
                    )
                    for recipient in notification_recipients
                    if recipient != request.user  # Don't notify the person who deleted it
                ]
                
                if notifications_to_create:
                    Notification.objects.bulk_create(notifications_to_create, batch_size=100)
                
                # Delete project updates related to this submission
                ProjectUpdate.objects.filter(submission=submission).delete()
                
                # If this submission is linked to an event, mark event as not having submission
                if submission.event:
                    submission.event.has_submission = False
                    submission.event.save()
                
                # Delete the submission
                project_id = project.id
                submission.delete()
                
                # Redirect with toast parameters
                from urllib.parse import quote
                return redirect(f'/projects/{project_id}/submission/?success=true&action=deleted&title={quote(form_name)}')

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
                submission.revision_count += 1
                submission.save()
        # New: Allow UESO/DIRECTOR/VP to approve directly from SUBMITTED if project leader has no college
        # BUT only if they are NOT involved in the project (not leader or provider)
        elif submission.status == 'SUBMITTED' and request.user.role in ["VP", "DIRECTOR", "UESO"]:
            # Check if project leader has no college
            project_leader_has_no_college = submission.project.project_leader and not submission.project.project_leader.college
            # Check if admin is NOT involved in the project
            is_not_project_member = (
                request.user.id != submission.project.project_leader.id and 
                not submission.project.providers.filter(id=request.user.id).exists()
            )
            if project_leader_has_no_college and is_not_project_member:
                if action == 'accept':
                    submission.status = 'APPROVED'
                    submission.authorized_by = request.user
                    submission.authorized_at = timezone.now()
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
                    submission.revision_count += 1
                    submission.save()
        elif submission.status == 'FORWARDED' and request.user.role in ["VP", "DIRECTOR", "UESO"]:
            # Check if admin is NOT involved in the project
            is_not_project_member = (
                request.user.id != submission.project.project_leader.id and 
                not submission.project.providers.filter(id=request.user.id).exists()
            )
            if is_not_project_member:
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
                    submission.rejection_count += 1
                    submission.save()
                
        # Create or update ProjectUpdate for key status changes that affect the project team
        if action in ['forward', 'accept', 'reject', 'request_revision'] and submission.project:
            # Notify project leader and providers about submission status changes
            users_to_notify = [submission.project.project_leader]
            if submission.project.providers.exists():
                users_to_notify.extend(submission.project.providers.all())
            
            for user in users_to_notify:
                if user:  # Ensure user exists
                    ProjectUpdate.objects.update_or_create(
                        user=user,
                        project=submission.project,
                        submission=submission,
                        status=f'{submission.status}',
                        defaults={
                            'viewed': False,
                            'updated_at': timezone.now(),
                        }
                    )
    from urllib.parse import quote
    submission_title = submission.downloadable.name if submission.downloadable else "Submission"
    return redirect(f'/projects/{pk}/submission/?success=true&action={action}&title={quote(submission_title)}')


@project_visibility_required
def project_expenses(request, pk):
    # messages is imported at the top
    # Sum and Decimal are imported at the top
    
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()

    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"

    project = get_object_or_404(Project, pk=pk)

    # Calculate Total Budget (Internal + External)
    try:
        # Ensure Decimal is used for calculation
        total_budget = (project.internal_budget or Decimal('0')) + (project.external_budget or Decimal('0'))
    except Exception:
        total_budget = Decimal('0')

    # Handle expense creation
    if request.method == 'POST' and request.user.is_authenticated:
        title = request.POST.get('reason') or request.POST.get('title')
        notes = request.POST.get('notes')
        amount_raw = request.POST.get('amount')
        receipt = request.FILES.get('receipt')
        
        try:
            # Accept decimals
            amount_val = Decimal(amount_raw) if amount_raw else Decimal('0')
        except Exception:
            messages.error(request, "Invalid amount entered. Please use a valid number.")
            return redirect(request.path)

        # Recompute used_budget for current check
        try:
            agg = ProjectExpense.objects.filter(project=project).aggregate(s=Sum('amount'))
            current_spent_total = agg.get('s') or Decimal('0')
        except Exception:
            current_spent_total = Decimal('0')

        # Budget Validation: Check if new expense exceeds total budget
        new_spent_total = current_spent_total + amount_val
        
        if total_budget <= Decimal('0'):
            # If total budget is zero or negative, no expenses are allowed
            messages.error(request, "Project budget is zero or negative. Cannot add expense.")
            return redirect(request.path)
            
        if new_spent_total > total_budget:
            # Block the expense if it exceeds the total budget
            messages.error(request, 
                           f"Expense exceeds total project budget of ₱{total_budget:,.2f}. "
                           f"Current spent: ₱{current_spent_total:,.2f}. "
                           f"Requested: ₱{amount_val:,.2f}.")
            return redirect(request.path)

        if title and amount_val > Decimal('0'):
            # If validation passes, create the expense
            ProjectExpense.objects.create(
                project=project,
                title=title,
                reason=notes,
                amount=amount_val,
                receipt=receipt,
                created_by=request.user,
            )
            
            # Update used_budget on the Project model
            project.used_budget = new_spent_total
            project.save(update_fields=['used_budget'])
            
            messages.success(request, f"Expense of ₱{amount_val:,.2f} successfully added.")
            return redirect(request.path)
        elif amount_val <= Decimal('0'):
             messages.error(request, "Amount must be greater than zero.")
             return redirect(request.path)


    # Dynamic budget figures based on Project fields
    # Use the calculated total_budget from above
    try:
        spent_total = project.used_budget or Decimal('0')
    except Exception:
        spent_total = Decimal('0')
        
    remaining_total = max(Decimal('0'), total_budget - spent_total)
    percent_remaining = 0
    if total_budget > Decimal('0'):
        try:
            # Cast to float for division, then back to int for percentage
            percent_remaining = int(round((float(remaining_total) / float(total_budget)) * 100))
        except Exception:
            percent_remaining = 0

    # Expenses data
    expenses = ProjectExpense.objects.filter(project=project).order_by('-date_incurred', '-created_at')
    return render(request, 'projects/project_expenses.html', {
        'project': project, 
        'base_template': base_template,
        'expenses': expenses,
        'remaining_total': remaining_total,
        'percent_remaining': percent_remaining,
        "ADMIN_ROLES": ADMIN_ROLES,
        "SUPERUSER_ROLES": SUPERUSER_ROLES,
        "FACULTY_ROLE": FACULTY_ROLE
    })


@project_visibility_required
def project_invoices(request, pk):
    """View for displaying receipt files (invoices)"""
    from django.contrib import messages
    
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()

    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"

    project = get_object_or_404(Project, pk=pk)

    # Handle expense creation (same logic as project_expenses)
    if request.method == 'POST' and request.user.is_authenticated:
        title = request.POST.get('reason') or request.POST.get('title')
        notes = request.POST.get('notes')
        amount_raw = request.POST.get('amount')
        receipt = request.FILES.get('receipt')
        try:
            amount_val = float(amount_raw or 0)
        except Exception:
            amount_val = 0
        if title and amount_val > 0:
            ProjectExpense.objects.create(
                project=project,
                title=title,
                reason=notes,
                amount=amount_val,
                receipt=receipt,
                created_by=request.user,
            )
            # Recompute used_budget as sum of expenses
            try:
                from django.db.models import Sum
                agg = ProjectExpense.objects.filter(project=project).aggregate(s=Sum('amount'))
                project.used_budget = agg.get('s') or 0
                project.save(update_fields=['used_budget'])
            except Exception:
                pass
            return redirect(request.path)

    # Expenses data with search and filter
    expenses = ProjectExpense.objects.filter(project=project)
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        from django.db.models import Q
        expenses = expenses.filter(
            Q(title__icontains=search_query) |
            Q(reason__icontains=search_query)
        )
    
    # Sorting functionality
    sort_by = request.GET.get('sort_by', 'date')
    order = request.GET.get('order', 'desc')
    
    # Map sort_by to actual field names
    sort_field_map = {
        'date': 'date_incurred',
        'title': 'title',
        'amount': 'amount',
    }
    
    sort_field = sort_field_map.get(sort_by, 'date_incurred')
    
    # Apply ordering
    if order == 'asc':
        expenses = expenses.order_by(sort_field, 'created_at')
    else:
        expenses = expenses.order_by(f'-{sort_field}', '-created_at')
    
    return render(request, 'projects/project_invoices.html', {
        'project': project, 
        'base_template': base_template,
        'expenses': expenses,
        "ADMIN_ROLES": ADMIN_ROLES,
        "SUPERUSER_ROLES": SUPERUSER_ROLES,
        "FACULTY_ROLE": FACULTY_ROLE
    })


@project_visibility_required
def project_evaluations(request, pk):
    ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE = get_role_constants()

    # Determine base template and access control
    user_role = getattr(request.user, 'role', None) if request.user.is_authenticated else None
    
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
        # Authenticated users with roles can see all projects
        project = get_object_or_404(Project, pk=pk)
    else:
        base_template = "base_public.html"
        # Non-authenticated users or users without admin roles can only see completed projects
        if not request.user.is_authenticated:
            project = get_object_or_404(Project, pk=pk, status='COMPLETED')
        else:
            project = get_object_or_404(Project, pk=pk)

    # Only authenticated users with required roles can submit evaluations
    if request.method == 'POST' and request.user.is_authenticated and user_role in ["UESO", "VP", "DIRECTOR", "PROGRAM_HEAD", "DEAN", "COORDINATOR", "FACULTY", "IMPLEMENTER"]:
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


@role_required(allowed_roles=["UESO", "VP", "DIRECTOR", "PROGRAM_HEAD", "DEAN", "COORDINATOR", "FACULTY", "IMPLEMENTER"], require_confirmed=True)
def edit_project_evaluation(request, pk, eval_id):
    project = get_object_or_404(Project, pk=pk)
    evaluation = get_object_or_404(ProjectEvaluation, pk=eval_id, project=project)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        if rating is not None and rating != "":
            try:
                evaluation.rating = int(rating)
            except Exception:
                pass
        evaluation.comment = comment
        evaluation.save()
    return redirect(f'/projects/{pk}/evaluations/')


@role_required(allowed_roles=["UESO", "VP", "DIRECTOR", "PROGRAM_HEAD", "DEAN", "COORDINATOR"], require_confirmed=True)
def delete_project_evaluation(request, pk, eval_id):
    project = get_object_or_404(Project, pk=pk)
    evaluation = get_object_or_404(ProjectEvaluation, pk=eval_id, project=project)
    if request.method in ['POST', 'GET']:
        try:
            evaluation.delete()
        except Exception:
            pass
    return redirect(f'/projects/{pk}/evaluations/')


########################################################################################################################


from django.views.decorators.http import require_POST
# Mark project as cancelled
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"], require_confirmed=True)
@require_POST
def cancel_project(request, pk):
    # timezone is imported at the top
    project = get_object_or_404(Project, pk=pk)
    project.status = 'CANCELLED'
    project.save()
    
    # Create project alerts for team members
    users_to_notify = [project.project_leader]
    if project.providers.exists():
        users_to_notify.extend(project.providers.all())
    
    for user in users_to_notify:
        if user:
            ProjectUpdate.objects.update_or_create(
                user=user,
                project=project,
                submission=None,  # No submission for project status changes
                status='CANCELLED',
                defaults={
                    'viewed': False,
                    'updated_at': timezone.now(),
                }
            )
    
    return redirect(f'/projects/{pk}/overview/')

# Undo cancel
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"], require_confirmed=True)
@require_POST
def undo_cancel_project(request, pk):
    # dtdate and timezone are imported at the top
    project = get_object_or_404(Project, pk=pk)
    today = dtdate.today()
    old_status = project.status
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
    
    # Create project alerts for team members if status changed
    if old_status != project.status:
        users_to_notify = [project.project_leader]
        if project.providers.exists():
            users_to_notify.extend(project.providers.all())
        
        for user in users_to_notify:
            if user:
                ProjectUpdate.objects.update_or_create(
                    user=user,
                    project=project,
                    submission=None,  # No submission for project status changes
                    status=project.status,
                    defaults={
                        'viewed': False,
                        'updated_at': timezone.now(),
                    }
                )
    
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


@role_required(allowed_roles=["FACULTY", "IMPLEMENTER"], require_confirmed=True)
def faculty_project(request):
    user = request.user

    # Filters
    sort_by = request.GET.get('sort_by', 'last_updated')
    order = request.GET.get('order', 'desc')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')

    
    projects = Project.objects.filter(
        models.Q(project_leader=user) | models.Q(providers=user)
    ).distinct()

    # Apply filters
    if status:
        projects = projects.filter(status=status)
    if date_from:
        projects = projects.filter(start_date__gte=date_from)
    if date_to:
        projects = projects.filter(start_date__lte=date_to)
    if search:
        projects = projects.filter(title__icontains=search)

    # Sorting
    if sort_by == 'progress':
        # For progress sort, convert to list and sort in Python
        projects_list = list(projects)
        projects = sorted(projects_list, key=lambda p: (p.progress[0] / p.progress[1]) if p.progress and p.progress[1] else 0, reverse=(order=='desc'))
    else:
        # Database sorting for other fields
        sort_map = {
            'title': 'title',
            'last_updated': 'updated_at',
            'start_date': 'start_date',
        }
        sort_field = sort_map.get(sort_by, 'updated_at')
        if order == 'desc':
            sort_field = '-' + sort_field
        projects = projects.order_by(sort_field)

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

    # Get recent status updates for this user's projects
    updates_qs = ProjectUpdate.objects.filter(user=user).order_by('-updated_at')[:10]
    alerts = []
    for update in updates_qs:
        # Build message text
        status_text = {
            'CANCELLED': 'has been cancelled',
            'COMPLETED': 'has been completed',
            'ONGOING': 'is now ongoing',
            'SCHEDULED': 'is now scheduled',
            'PROJECT_ASSIGNED': 'you have been assigned to',
            'PENDING': 'requires a new submission',
            'FORWARDED': 'submission has been forwarded to UESO',
            'APPROVED': 'submission has been approved',
            'REJECTED': 'submission has been rejected',
            'REVISION_REQUESTED': 'submission requires revision',
        }.get(update.status, f'status updated to {update.status.replace("_", " ").lower()}')
        alerts.append({
            'project_id': update.project.id,
            'submission_id': update.submission.id if update.submission else None,
            'title': update.project.title,
            'status': update.status,
            'viewed': update.viewed,
            'updated_at': update.updated_at,
            'message': f"Your project '{update.project.title}' {status_text}",
        })

    # Status choices for filter dropdown
    status_choices = Project.STATUS_CHOICES

    return render(request, 'projects/faculty_project.html', {
        'projects': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'page_range': page_range,
        'my_alerts': alerts,
        'status_choices': status_choices,
        'sort_by': sort_by,
        'order': order,
        'status': status,
        'date_from': date_from,
        'date_to': date_to,
        'search': search,
        'querystring': request.GET.urlencode().replace('&page='+str(page_obj.number), '') if page_obj else '',
    })


@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"], require_confirmed=True)
def admin_project(request):
    ADMIN_ROLES = ["VP", "DIRECTOR", "UESO"]
    SUPERUSER_ROLES = ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]

    # Filters
    sort_by = request.GET.get('sort_by', 'last_updated')
    order = request.GET.get('order', 'desc')
    college = request.GET.get('college', '')
    campus = request.GET.get('campus', '')
    agenda = request.GET.get('agenda', '')
    goal_id = request.GET.get('goal', '')
    status = request.GET.get('status', '')
    year = request.GET.get('year', '')
    quarter = request.GET.get('quarter', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')

    if request.user.role in ADMIN_ROLES:
        projects = Project.objects.all()
    elif request.user.role in SUPERUSER_ROLES:
        # For PROGRAM_HEAD, DEAN, COORDINATOR: limit to their college if applicable
        user_college = getattr(request.user, 'college', None)
        if user_college:
            projects = Project.objects.filter(project_leader__college=user_college)
        else:
            projects = Project.objects.all()

    # Apply filters
    if college:
        projects = projects.filter(project_leader__college__id=college)
    if campus:
        projects = projects.filter(project_leader__campus=campus)
    if agenda:
        projects = projects.filter(agenda__id=agenda)
    # Apply goal-based filters (maps a Goal's criteria to project list)
    if goal_id:
        try:
            goal_obj = Goal.objects.get(pk=int(goal_id))
            if goal_obj.agenda_id:
                projects = projects.filter(agenda__id=goal_obj.agenda_id)
            if goal_obj.project_status:
                projects = projects.filter(status=goal_obj.project_status)
            if goal_obj.sdg_id:
                projects = projects.filter(sdgs__id=goal_obj.sdg_id)
        except (Goal.DoesNotExist, ValueError):
            pass
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
    if date_from:
        projects = projects.filter(start_date__gte=date_from)
    if date_to:
        projects = projects.filter(start_date__lte=date_to)
    if search:
        projects = projects.filter(title__icontains=search)

    # Sorting
    if sort_by == 'progress':
        # For progress sort, convert to list and sort in Python
        projects_list = list(projects)
        projects = sorted(projects_list, key=lambda p: (p.progress[0] / p.progress[1]) if p.progress and p.progress[1] else 0, reverse=(order=='desc'))
    else:
        # Database sorting for other fields
        sort_map = {
            'title': 'title',
            'last_updated': 'updated_at',
            'start_date': 'start_date',
        }
        sort_field = sort_map.get(sort_by, 'updated_at')
        if order == 'desc':
            sort_field = '-' + sort_field
        projects = projects.order_by(sort_field)

    # Filter options
    colleges = College.objects.all()
    campuses = Campus.objects.all()
    status_choices = Project.STATUS_CHOICES
    agendas = Agenda.objects.all()
    # Get available years from projects that exist
    years = list(set([d.year for d in Project.objects.dates('start_date', 'year')]))
    years.sort(reverse=True)

    # Pagination
    paginator = Paginator(projects, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(page_obj.number)

    # Check for success message from add_project
    success = request.GET.get('success', '')
    new_project_id = request.GET.get('new_project_id', '')
    project_title = request.GET.get('project_title', '')

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
        'goal': goal_id,
        'status': status,
        'year': year,
        'quarter': quarter,
        'date_from': date_from,
        'date_to': date_to,
        'search': search,
        'page_obj': page_obj,
        'paginator': paginator,
        'page_range': page_range,
        'querystring': request.GET.urlencode().replace('&page='+str(page_obj.number), '') if page_obj else '',
        "ADMIN_ROLES": ADMIN_ROLES,
        "SUPERUSER_ROLES": SUPERUSER_ROLES,
        'success': success,
        'new_project_id': new_project_id,
        'project_title': project_title,
    })


########################################################################################################################


# timezone is imported at the top


@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def add_project_view(request):
    error = None
    # All user roles except CLIENT and IMPLEMENTER can be project leader
    faculty_users = User.objects.filter(is_confirmed=True).exclude(role__in=[User.Role.CLIENT, User.Role.IMPLEMENTER])
    # All user roles except CLIENT can be provider
    provider_users = User.objects.filter(is_confirmed=True).exclude(role=User.Role.CLIENT)
    agendas = Agenda.objects.all()
    sdgs = SustainableDevelopmentGoal.objects.all()
    colleges = College.objects.all()
    campus_choices = Campus.objects.all()

    logistics_type = 'BOTH'
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Validate budget before saving
                # CollegeBudget, datetime, Decimal are imported at the top
                
                project_leader = form.cleaned_data.get('project_leader')
                logistics_type_value = form.cleaned_data['logistics_type']
                internal_budget_value = form.cleaned_data.get('internal_budget', Decimal('0'))
                
                # Check budget if logistics type involves internal funding
                if logistics_type_value in ['BOTH', 'INTERNAL'] and internal_budget_value > 0:
                    if not project_leader:
                        error = "Project leader is required for budget validation."
                        raise ValueError(error)
                    
                    if not project_leader.college:
                        error = f"Project leader {project_leader.get_full_name()} does not have an assigned college. Budget cannot be validated."
                        raise ValueError(error)
                    
                    # Get current fiscal year
                    current_year = str(datetime.now().year)
                    
                    # Get college budget for current fiscal year
                    try:
                        college_budget = CollegeBudget.objects.get(
                            college=project_leader.college,
                            fiscal_year=current_year,
                            status='ACTIVE'
                        )
                    except CollegeBudget.DoesNotExist:
                        error = f"No active budget allocation found for {project_leader.college.name} in fiscal year {current_year}. Cannot create project with internal budget."
                        raise ValueError(error)
                    
                    # Check if budget is sufficient
                    uncommitted_budget = college_budget.uncommitted_remaining
                    # Use Decimal formatting placeholder for budget check
                    if internal_budget_value > uncommitted_budget:
                        error = f"Insufficient budget for {project_leader.college.name}. Requested: ₱{internal_budget_value:,.2f}, Available: ₱{uncommitted_budget:,.2f}"
                        raise ValueError(error)
                
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
                project.save()

                # Create alerts for project members about being added to the project
                from .models import ProjectUpdate
                project_members = list(project.providers.all())  # Get all project providers
                if project.project_leader:  # Add project leader if exists
                    project_members.append(project.project_leader)
                
                for member in project_members:
                    ProjectUpdate.objects.create(
                        user=member,
                        project=project,
                        submission=None,  # No submission for project creation alerts
                        status='PROJECT_ASSIGNED',
                        viewed=False,
                        updated_at=timezone.now()
                    )

                # Redirect to admin_project with success message and new project ID
                from urllib.parse import quote
                return redirect(f'/projects/?success=true&new_project_id={project.id}&project_title={quote(project.title)}')
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


def check_college_budget(request):
    """AJAX endpoint to validate college budget availability"""
    # JsonResponse, CollegeBudget, datetime, Decimal are imported at the top
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    project_leader_id = request.GET.get('project_leader_id')
    internal_budget = request.GET.get('internal_budget', '0')
    
    if not project_leader_id:
        return JsonResponse({'error': 'Project leader is required'}, status=400)
    
    try:
        # Get project leader
        leader = User.objects.select_related('college').get(id=project_leader_id)
        
        if not leader.college:
            return JsonResponse({
                'valid': False,
                'error': 'Selected project leader does not have an assigned college.',
                'college_name': None,
                'total_budget': 0,
                'uncommitted': 0,
                'remaining': 0
            })
        
        # Parse the internal budget
        try:
            requested_budget = Decimal(internal_budget) if internal_budget else Decimal('0')
        except:
            return JsonResponse({
                'valid': False,
                'error': 'Invalid budget amount.',
                'college_name': leader.college.name,
                'total_budget': 0,
                'uncommitted': 0,
                'remaining': 0
            })
        
        # Get current fiscal year
        current_year = str(datetime.now().year)
        
        # Get college budget for current fiscal year
        try:
            college_budget = CollegeBudget.objects.get(
                college=leader.college,
                fiscal_year=current_year,
                status='ACTIVE'
            )
        except CollegeBudget.DoesNotExist:
            return JsonResponse({
                'valid': False,
                'error': f'No active budget allocation found for {leader.college.name} in fiscal year {current_year}.',
                'college_name': leader.college.name,
                'total_budget': 0,
                'uncommitted': 0,
                'remaining': 0
            })
        
        # Calculate available budget
        uncommitted_budget = college_budget.uncommitted_remaining
        remaining_after_project = uncommitted_budget - requested_budget
        
        # Check if requested budget exceeds available
        # Use float(Decimal) for JsonResponse serialization
        if requested_budget > uncommitted_budget:
            return JsonResponse({
                'valid': False,
                'error': f'Requested budget (₱{requested_budget:,.2f}) exceeds available budget (₱{uncommitted_budget:,.2f}) for {leader.college.name}.',
                'college_name': leader.college.name,
                'total_budget': float(college_budget.total_assigned),
                'uncommitted': float(uncommitted_budget),
                'remaining': float(remaining_after_project),
                'requested': float(requested_budget)
            })
        
        # Budget is valid
        return JsonResponse({
            'valid': True,
            'message': f'Budget allocation is valid. Available: ₱{uncommitted_budget:,.2f}',
            'college_name': leader.college.name,
            'total_budget': float(college_budget.total_assigned),
            'uncommitted': float(uncommitted_budget),
            'remaining': float(remaining_after_project),
            'requested': float(requested_budget)
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'valid': False,
            'error': 'Project leader not found.',
            'college_name': None,
            'total_budget': 0,
            'uncommitted': 0,
            'remaining': 0
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'valid': False,
            'error': f'Error checking budget: {str(e)}',
            'college_name': None,
            'total_budget': 0,
            'uncommitted': 0,
            'remaining': 0
        }, status=500)


@role_required(allowed_roles=["UESO", "VP", "DIRECTOR"], require_confirmed=True)
def delete_project(request, pk):
    """Delete a project"""
    from django.contrib import messages
    from system.logs.models import LogEntry
    from system.notifications.models import Notification
    from system.users.models import User
    
    if request.method == "POST":
        try:
            project = Project.objects.select_related('project_leader__college').prefetch_related('providers').get(pk=pk)
            project_title = project.title
            project_leader = project.project_leader
            project_college = project_leader.college if project_leader else None
            
            # Get all people involved for notifications
            notification_recipients = []
            if project_leader:
                notification_recipients.append(project_leader)
            notification_recipients.extend(list(project.providers.all()))
            
            # Also notify coordinator of the same college
            if project_college:
                coordinators = User.objects.filter(
                    role='COORDINATOR',
                    college=project_college,
                    is_confirmed=True,
                    is_active=True
                )
                notification_recipients.extend(coordinators)
            
            # Notify UESO, Director, VP
            supervisors = User.objects.filter(
                role__in=['UESO', 'DIRECTOR', 'VP'],
                is_confirmed=True,
                is_active=True
            )
            notification_recipients.extend(supervisors)
            
            # Remove duplicates
            notification_recipients = list(set(notification_recipients))
            
            # Create log entry BEFORE deletion (so we still have the project data)
            log_entry = LogEntry.objects.create(
                user=request.user,
                action='DELETE',
                model='Project',
                object_id=project.id,
                object_repr=project_title,
                details=f"Project '{project_title}' and all related data (submissions, events, files) have been deleted by {request.user.get_full_name()}",
                url='',  # No URL since the project no longer exists
                is_notification=False  # We'll create notifications manually
            )
            
            # Create notifications manually for all involved users (except the actor)
            notifications_to_create = [
                Notification(
                    recipient=recipient,
                    actor=request.user,
                    action='DELETE',
                    model='Project',
                    object_id=project.id,
                    object_repr=project_title,
                    details=f"Project '{project_title}' has been deleted",
                    url='',
                )
                for recipient in notification_recipients
                if recipient != request.user  # Don't notify the person who deleted it
            ]
            
            if notifications_to_create:
                Notification.objects.bulk_create(notifications_to_create, batch_size=100)
            
            # Delete the project (this will cascade delete related submissions, events, etc.)
            project.delete()
            
            messages.success(request, f'Project "{project_title}" has been deleted successfully.')
            
            # Redirect with toast parameters
            from urllib.parse import quote
            return redirect(f'/projects/?success=true&action=deleted&title={quote(project_title)}')
        except Project.DoesNotExist:
            messages.error(request, 'Project not found.')
    
    return redirect('project_dispatcher')