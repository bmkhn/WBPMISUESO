from django.shortcuts import render, redirect
from system.users.decorators import role_required
from shared.projects.models import Project
from shared.downloadables.models import Downloadable
from .models import Submission
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib import messages


@role_required(allowed_roles=["UESO", "VP", "DIRECTOR", "COORDINATOR"], require_confirmed=True)
def submission_admin_view(request):
    from django.db.models import Case, When, Value, IntegerField
    user_role = getattr(request.user, 'role', None)
    # Optimize query with select_related
    submissions = Submission.objects.select_related(
        'project',
        'project__project_leader',
        'project__project_leader__college',
        'downloadable',
        'event',
        'reviewed_by'
    )
    
    # Filter submissions by college for COORDINATOR
    if user_role == "COORDINATOR" and request.user.college:
        submissions = submissions.filter(project__project_leader__college=request.user.college)

    # Filters
    sort_by = request.GET.get('sort_by', 'deadline')
    order = request.GET.get('order', 'desc')
    status = request.GET.get('status', '')
    required_form = request.GET.get('required_form', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '').strip()

    # Apply filters
    if status:
        submissions = submissions.filter(status__iexact=status)
    if required_form:
        submissions = submissions.filter(downloadable__id=required_form)
    if date_from:
        submissions = submissions.filter(deadline__date__gte=date_from)
    if date_to:
        submissions = submissions.filter(deadline__date__lte=date_to)
    if search:
        submissions = submissions.filter(project__title__icontains=search)

    submissions = submissions.distinct()

    # Custom ordering for roles
    if user_role in ["COORDINATOR", "PROGRAM_HEAD", "DEAN"]:
        submissions = submissions.filter(status__in=["SUBMITTED", "REVISION_REQUESTED", "FORWARDED"])
        submissions = submissions.annotate(
            status_priority=Case(
                When(status="SUBMITTED", then=Value(0)),
                When(status="REVISION_REQUESTED", then=Value(1)),
                When(status="FORWARDED", then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            )
        ).order_by('status_priority', '-created_at')
    elif user_role in ["UESO", "VP", "DIRECTOR"]:
        submissions = submissions.annotate(
            status_priority=Case(
                When(status="FORWARDED", then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by('status_priority', '-created_at')
    else:
        submissions = submissions.order_by('-created_at')

    # Filter Options - optimize with only()
    all_statuses = [status[1] for status in Submission.SUBMISSION_STATUS_CHOICES]
    all_forms = Downloadable.objects.filter(is_submission_template=True).only('id', 'file')

    # Pagination
    paginator = Paginator(submissions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(page_obj.number)

    return render(request, 'submissions/submissions.html', {
        'search': search,
        'sort_by': sort_by,
        'order': order,
        'all_statuses': all_statuses,
        'status': status,
        'all_forms': all_forms,
        'required_form': required_form,
        'date_from': date_from,
        'date_to': date_to,
        'page_obj': page_obj,
        'paginator': paginator,
        'page_range': page_range,
        'querystring': request.GET.urlencode().replace('&page='+str(page_obj.number), '') if page_obj else '',
    })


@role_required(allowed_roles=["UESO", "VP", "DIRECTOR"], require_confirmed=True)
def add_submission_requirement(request, project_id=None):
    from shared.projects.models import ProjectEvent
    import json
    
    # Optimize queries
    projects = Project.objects.exclude(status__in=['CANCELLED', 'COMPLETED']).select_related(
        'project_leader',
        'project_leader__college'
    ).only('id', 'title', 'start_date', 'estimated_events', 'project_leader')
    downloadables = Downloadable.objects.filter(is_submission_template=True).only('id', 'file', 'submission_type')
    
    # Pre-selected project if coming from project page
    preselected_project = None
    if project_id:
        try:
            preselected_project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            preselected_project = None
    
    # Get event availability and progress for each project
    project_event_availability = {}
    for project in projects:
        available_events = ProjectEvent.objects.filter(
            project=project, 
            placeholder=False, 
            has_submission=False
        ).order_by('-created_at')
        
        events_list = []
        for event in available_events:
            events_list.append({
                'id': event.id,
                'title': event.title,
                'datetime': event.datetime.strftime('%Y-%m-%d %H:%M') if event.datetime else 'No date set'
            })
        
        # Check if all events are completed (event_progress == estimated_events)
        all_events_completed = (project.event_progress >= project.estimated_events) if project.estimated_events > 0 else False
        
        project_event_availability[project.id] = {
            'has_available_events': available_events.exists(),
            'available_events': events_list,
            'all_events_completed': all_events_completed,
            'event_progress': project.event_progress,
            'estimated_events': project.estimated_events,
            'start_date': project.start_date.strftime('%Y-%m-%d') if project.start_date else None
        }
    
    # Convert to JSON for template
    project_event_availability_json = json.dumps(project_event_availability)

    if request.method == "POST":
        project_id = request.POST.get('project')
        downloadable_ids = request.POST.getlist('downloadables')
        deadline = request.POST.get('deadline')
        notes = request.POST.get('notes')
        selected_event_id = request.POST.get('selected_event')  # Get selected event for event submissions
        
        error = None
        if not project_id:
            error = "A project is required."
        if not downloadable_ids:
            error = "At least one downloadable is required."
        if not deadline:
            error = "Deadline is required."
        if error:
            return render(request, 'submissions/add_submissions.html', {
                'projects': projects,
                'downloadables': downloadables,
                'project_event_availability_json': project_event_availability_json,
                'preselected_project': preselected_project,
                'error': error,
            })
        # Create a Submission for each downloadable
        project = Project.objects.get(id=project_id)
        for downloadable_id in downloadable_ids:
            downloadable = Downloadable.objects.get(id=downloadable_id)
            
            # For event-type submissions, link to selected event
            event = None
            if downloadable.submission_type == 'event' and selected_event_id:
                try:
                    event = ProjectEvent.objects.get(
                        id=selected_event_id,
                        project=project, 
                        placeholder=False, 
                        has_submission=False
                    )
                    # Mark this event as having a submission
                    event.has_submission = True
                    event.save()
                except ProjectEvent.DoesNotExist:
                    pass
            
            submission = Submission.objects.create(
                project=project,
                downloadable=downloadable,
                event=event,  # Link to the selected event if it's an event submission
                deadline=deadline,
                created_by=request.user,
                notes=notes,
                status='PENDING',
                created_at=timezone.now()
            )
            
            # Create alert for project members about new submission requirement
            from shared.projects.models import ProjectUpdate
            project_members = list(project.providers.all())  # Get all project providers
            if project.project_leader:  # Add project leader if exists
                project_members.append(project.project_leader)
            
            for member in project_members:
                ProjectUpdate.objects.create(
                    user=member,
                    project=project,
                    submission=submission,
                    status='PENDING',
                    viewed=False,
                    updated_at=timezone.now()
                )
            

        
        # Redirect with toast parameters
        from urllib.parse import quote
        count = len(downloadable_ids)
        return redirect(f'/submissions/?success=true&action=created&count={count}&title={quote(project.title)}')
    else:
        return render(request, 'submissions/add_submissions.html', {
            'projects': projects,
            'downloadables': downloadables,
            'project_event_availability_json': project_event_availability_json,
            'preselected_project': preselected_project,
        })


def add_submission_view(request):
    return render(request, 'submissions/add_submissions.html')


# Include this file just to be sure