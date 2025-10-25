from django.shortcuts import render, redirect
from system.users.decorators import role_required
from shared.projects.models import Project
from shared.downloadables.models import Downloadable
from .models import Submission
from django.utils import timezone
from django.core.paginator import Paginator


@role_required(allowed_roles=["UESO", "VP", "DIRECTOR", "COORDINATOR"])
def submission_admin_view(request):
    from django.db.models import Case, When, Value, IntegerField
    user_role = getattr(request.user, 'role', None)
    submissions = Submission.objects.all()

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

    # Filter Options
    all_statuses = [status[1] for status in Submission.SUBMISSION_STATUS_CHOICES]
    all_forms = Downloadable.objects.filter(is_submission_template=True)

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


@role_required(allowed_roles=["UESO", "VP", "DIRECTOR"])
def add_submission_requirement(request):
    projects = Project.objects.exclude(status__in=['CANCELLED', 'COMPLETED'])
    downloadables = Downloadable.objects.filter(is_submission_template=True)

    if request.method == "POST":
        project_id = request.POST.get('project')
        downloadable_ids = request.POST.getlist('downloadables')
        deadline = request.POST.get('deadline')
        notes = request.POST.get('notes')
        
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
                'error': error,
            })
        # Create a Submission for each downloadable
        project = Project.objects.get(id=project_id)
        for downloadable_id in downloadable_ids:
            submission = Submission.objects.create(
                project=project,
                downloadable=Downloadable.objects.get(id=downloadable_id),
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
            

        
        return render(request, 'submissions/add_submissions.html', {
            'projects': projects,
            'downloadables': downloadables,
            'success': True,
        })
    else:
        return render(request, 'submissions/add_submissions.html', {
            'projects': projects,
            'downloadables': downloadables,
        })


def add_submission_view(request):
    return render(request, 'submissions/add_submissions.html')
