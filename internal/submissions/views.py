from django.shortcuts import render, redirect
from system.users.decorators import role_required
from shared.projects.models import Project
from shared.downloadables.models import Downloadable
from .models import SubmissionRequirement
from django.utils import timezone
from django.core.paginator import Paginator


@role_required(allowed_roles=["UESO", "VP", "DIRECTOR"])
def submission_admin_view(request):
    submissions = SubmissionRequirement.objects.all()

    # Filters
    sort_by = request.GET.get('sort_by', 'deadline')
    order = request.GET.get('order', 'desc')
    status = request.GET.get('status', '')
    required_form = request.GET.get('required_form', '')
    date = request.GET.get('date', '')
    search = request.GET.get('search', '').strip()

    # Apply filters
    if status:
        submissions = submissions.filter(status__iexact=status)
    if required_form:
        submissions = submissions.filter(downloadables__id=required_form)
    if date:
        submissions = submissions.filter(deadline__date=date)
    if search:
        submissions = submissions.filter(projects__title__icontains=search)

    submissions = submissions.distinct()

    # Sorting
    sort_map = {
        'deadline': 'deadline',
        # 'date_submitted': '', 
        'title': 'projects__title',
        'status': 'status',
        'required_form': 'downloadables__name',
    }
    sort_field = sort_map.get(sort_by, 'deadline')
    if sort_field:
        if order == 'desc':
            sort_field = '-' + sort_field
        submissions = submissions.order_by(sort_field)

    # Filter Options
    all_statuses = [status[1] for status in SubmissionRequirement.SUBMISSION_STATUS_CHOICES]
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
        'date': date,
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
        # Create SubmissionRequirement
        sr = SubmissionRequirement.objects.create(
            project=Project.objects.get(id=project_id),
            deadline=deadline,
            created_by=request.user,
            status='pending',
            created_at=timezone.now()
        )
        sr.downloadables.set(Downloadable.objects.filter(id__in=downloadable_ids))
        sr.save()
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
