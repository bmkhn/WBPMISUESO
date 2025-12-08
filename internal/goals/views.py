from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Count
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.utils.dateparse import parse_date
from system.users.decorators import role_required
from .models import Goal
from internal.agenda.models import Agenda
from shared.projects.models import Project, SustainableDevelopmentGoal
# Forms are no longer used; the page uses JSON API endpoints

@role_required(allowed_roles=["DIRECTOR", "VP", "UESO"])
def goal_view(request):
    # Simple view that just renders the static template
    return render(request, 'goals/goals.html')

    


def _serialize_goal(goal: Goal) -> dict:
    """Return a JSON-serializable dict for the Goal expected by the frontend.
    Progress is computed dynamically from matching projects vs target.
    """
    progress = 0
    try:
        total_target = goal.target_value or 0
        if total_target > 0:
            matched = _count_matching_projects(goal)
            progress = max(0, min(100, int(round(matched * 100 / total_target))))
    except Exception:
        progress = 0

    # Get SDG IDs - prefer new many-to-many field, fallback to old single field
    sdg_ids = list(goal.sdgs.values_list('id', flat=True)) if goal.sdgs.exists() else []
    if not sdg_ids and goal.sdg_id:
        sdg_ids = [goal.sdg_id]
    
    return {
        'id': goal.id,
        'title': goal.title,
        # Frontend expects these fields; not in model → return defaults
        'agenda': getattr(goal.agenda, 'id', None),
        'sdg': sdg_ids[0] if sdg_ids else None,  # Keep for backward compatibility
        'sdgs': sdg_ids,  # New field with all SDG IDs
        'status': goal.status,
        'goal_number': goal.target_value or 0,
        'deadline': goal.target_date.isoformat() if goal.target_date else None,
        'progress': progress,
    }


def _count_matching_projects(goal: Goal) -> int:
    qs = Project.objects.all()
    if goal.agenda_id:
        qs = qs.filter(agenda_id=goal.agenda_id)
    # Handle multiple SDGs - if any SDGs are selected, filter by them
    if goal.sdgs.exists():
        qs = qs.filter(sdgs__in=goal.sdgs.all()).distinct()
    elif goal.sdg_id:  # Fallback to old single SDG field for backward compatibility
        qs = qs.filter(sdgs=goal.sdg_id)
    if goal.project_status:
        qs = qs.filter(status=goal.project_status)
    return qs.count()


@role_required(allowed_roles=["DIRECTOR", "VP", "UESO"])
@require_http_methods(["GET", "POST"])
@csrf_protect
def api_goals(request):
    """GET: list goals; POST: create goal.
    Frontend hits /goals/api/goals/ with JSON body for POST.
    """
    if request.method == 'GET':
        goals = Goal.objects.all().order_by('-created_at')
        response = JsonResponse({'success': True, 'goals': [_serialize_goal(g) for g in goals]})
        # Prevent caching to ensure fresh data
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    # POST create
    try:
        import json
        payload = json.loads(request.body or '{}')
    except Exception:
        payload = {}

    title = (payload.get('title') or '').strip()
    goal_number = payload.get('goal_number') or 0
    deadline_str = payload.get('deadline')
    status = payload.get('status') or 'ACTIVE'
    agenda_val = payload.get('agenda')
    sdg_val = payload.get('sdg')
    project_status_filter = payload.get('status')  # UI sends project status in same field

    if not title:
        return JsonResponse({'success': False, 'error': 'Title is required'}, status=400)

    deadline = parse_date(deadline_str) if deadline_str else None

    goal = Goal(
        title=title,
        target_value=int(goal_number) if str(goal_number).isdigit() else 0,
        current_value=0,
        unit='items',
        status=status,
        created_by=request.user,
        target_date=deadline,
    )
    # Persist filters if provided
    try:
        if agenda_val and str(agenda_val).isdigit():
            goal.agenda_id = int(agenda_val)
    except Exception:
        pass
    try:
        if sdg_val and str(sdg_val).isdigit():
            goal.sdg_id = int(sdg_val)
    except Exception:
        pass
    if project_status_filter and project_status_filter != 'all':
        goal.project_status = project_status_filter
    goal.save()

    return JsonResponse({'success': True, 'goal': _serialize_goal(goal)}, status=201)


@role_required(allowed_roles=["DIRECTOR", "VP", "UESO"])
@require_http_methods(["PUT", "DELETE"])
@csrf_protect
def api_goal_detail(request, goal_id: int):
    goal = get_object_or_404(Goal, id=goal_id)

    if request.method == 'DELETE':
        goal.delete()
        return JsonResponse({'success': True})

    # PUT update
    try:
        import json
        payload = json.loads(request.body or '{}')
    except Exception:
        payload = {}

    title = payload.get('title')
    goal_number = payload.get('goal_number')
    deadline_str = payload.get('deadline')
    status = payload.get('status')
    agenda_val = payload.get('agenda')
    sdg_val = payload.get('sdg')
    project_status_filter = payload.get('status')

    if title is not None:
        goal.title = title.strip()
    if goal_number is not None:
        try:
            goal.target_value = int(goal_number)
        except Exception:
            pass
    if deadline_str is not None:
        goal.target_date = parse_date(deadline_str)
    if status is not None:
        goal.status = status
    # Update persisted filters
    try:
        if agenda_val is not None:
            goal.agenda_id = int(agenda_val) if str(agenda_val).isdigit() else None
    except Exception:
        pass
    try:
        if sdg_val is not None:
            goal.sdg_id = int(sdg_val) if str(sdg_val).isdigit() else None
    except Exception:
        pass
    if project_status_filter is not None:
        goal.project_status = None if project_status_filter == 'all' else project_status_filter

    goal.save()
    return JsonResponse({'success': True, 'goal': _serialize_goal(goal)})


@role_required(allowed_roles=["DIRECTOR", "VP", "UESO"])
@require_http_methods(["GET"])
def api_goal_qualifiers(request, goal_id: int):
    """Return projects matching this goal's filters so the UI can list qualifiers-like rows."""
    goal = get_object_or_404(Goal, id=goal_id)
    qs = Project.objects.all()
    if goal.agenda_id:
        qs = qs.filter(agenda_id=goal.agenda_id)
    # Handle multiple SDGs - if any SDGs are selected, filter by them
    if goal.sdgs.exists():
        qs = qs.filter(sdgs__in=goal.sdgs.all()).distinct()
    elif goal.sdg_id:  # Fallback to old single SDG field for backward compatibility
        qs = qs.filter(sdgs=goal.sdg_id)
    if goal.project_status:
        qs = qs.filter(status=goal.project_status)

    rows = []
    for p in qs.select_related('project_leader').order_by('-start_date'):
        rows.append({
            'title': p.title,
            'team_leader': getattr(p.project_leader, 'username', '') if p.project_leader else '',
            'start_date': p.start_date.isoformat() if p.start_date else '',
            'status': p.get_status_display(),
        })
    return JsonResponse({'success': True, 'projects': rows})


@role_required(allowed_roles=["DIRECTOR", "VP", "UESO"])
@require_http_methods(["GET"])
def api_goal_filters(request):
    """Return distinct filter values present in the database for agendas, sdgs and project status."""
    # Include all agendas so newly added ones appear immediately (newest first)
    agendas_qs = Agenda.objects.all().order_by('-created_at', '-id').values("id", "name")

    # SDGs that are linked to at least one project
    sdgs_qs = SustainableDevelopmentGoal.objects.filter(projects__isnull=False).distinct().values("id", "goal_number", "name")

    # Project status values currently present
    status_codes = Project.objects.values_list("status", flat=True).distinct()
    status_display_map = dict(Project.STATUS_CHOICES)
    statuses = [
        {
            "code": code,
            "label": status_display_map.get(code, code)
        }
        for code in status_codes
        if code
    ]

    return JsonResponse({
        "success": True,
        "agendas": list(agendas_qs),
        "sdgs": list(sdgs_qs),
        "statuses": statuses,
    })


@role_required(allowed_roles=["DIRECTOR", "VP", "UESO"])
@require_http_methods(["GET"])
def api_sdg_distribution(request):
    """
    Return distribution of projects by SDG as percentages.

    A project can belong to multiple SDGs (many-to-many), so:
    - Each project is counted once *per SDG* it is linked to
    - Percent is based on distinct projects that have at least one SDG
      so multiple-SDG projects still appear in every relevant SDG slice.
    """
    # All projects that are linked to at least one SDG
    base_qs = Project.objects.filter(sdgs__isnull=False).distinct()
    total_projects = base_qs.count()

    if total_projects == 0:
        return JsonResponse({
            "success": True,
            "labels": [],
            "percents": [],
            "counts": [],
            "total_projects": 0,
        })

    # Count how many distinct projects are attached to each SDG
    sdg_counts = (
        SustainableDevelopmentGoal.objects
        .filter(projects__in=base_qs)
        .annotate(project_count=Count("projects", distinct=True))
        .order_by("goal_number")
    )

    labels = []
    percents = []
    counts = []

    for sdg in sdg_counts:
        count = sdg.project_count or 0
        percent = round((count * 100.0) / total_projects, 1) if total_projects > 0 else 0
        labels.append(f"SDG {sdg.goal_number} – {sdg.name}")
        percents.append(percent)
        counts.append(count)

    return JsonResponse({
        "success": True,
        "labels": labels,
        "percents": percents,
        "counts": counts,
        "total_projects": total_projects,
    })


# ===== Server-rendered Add/Edit pages (separate HTML like Agenda) =====
@role_required(allowed_roles=["DIRECTOR", "VP", "UESO"])
@csrf_protect
def add_goal_view(request):
    agendas = Agenda.objects.all().order_by('-created_at', '-id')
    sdgs = SustainableDevelopmentGoal.objects.all().order_by('goal_number')
    status_display_map = dict(Project.STATUS_CHOICES)
    statuses = [{"code": code, "label": status_display_map.get(code, code)} for code, _ in Project.STATUS_CHOICES]

    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        goal_number = request.POST.get('goal_number') or '0'
        deadline = request.POST.get('deadline') or ''
        agenda_id = request.POST.get('agenda') or ''
        sdg_ids = request.POST.getlist('sdgs')  # Get multiple SDG IDs
        project_status = request.POST.get('project_status') or ''

        errors = {}
        if not title:
            errors['title'] = 'Title is required.'
        try:
            goal_number_int = int(goal_number)
            if goal_number_int <= 0:
                errors['goal_number'] = 'Enter a positive number.'
        except Exception:
            errors['goal_number'] = 'Enter a valid number.'
        if not deadline:
            errors['deadline'] = 'Deadline is required.'

        if not errors:
            from django.utils.dateparse import parse_date
            g = Goal(
                title=title,
                target_value=goal_number_int,
                current_value=0,
                unit='items',
                status='ACTIVE',
                created_by=request.user,
                target_date=parse_date(deadline),
            )
            if agenda_id.isdigit():
                g.agenda_id = int(agenda_id)
            if project_status and project_status != 'all':
                g.project_status = project_status
            g.save()
            
            # Set multiple SDGs
            if sdg_ids:
                valid_sdg_ids = [int(sid) for sid in sdg_ids if sid.isdigit()]
                if valid_sdg_ids:
                    try:
                        g.sdgs.set(valid_sdg_ids)
                    except Exception:
                        # Fallback if migration hasn't been run yet
                        if valid_sdg_ids:
                            g.sdg_id = valid_sdg_ids[0]
                            g.save()
            
            # Redirect with success parameter to trigger page reload
            return redirect('goal')

        return render(request, 'goals/add_goal.html', {
            'agendas': agendas,
            'sdgs': sdgs,
            'statuses': statuses,
            'errors': errors,
            'form': {
                'title': title,
                'goal_number': goal_number,
                'deadline': deadline,
                'agenda': agenda_id,
                'sdgs': sdg_ids,
                'project_status': project_status,
            },
        })

    return render(request, 'goals/add_goal.html', {
        'agendas': agendas,
        'sdgs': sdgs,
        'statuses': statuses,
    })


@role_required(allowed_roles=["DIRECTOR", "VP", "UESO"])
@csrf_protect
def edit_goal_view(request, goal_id: int):
    goal = get_object_or_404(Goal, id=goal_id)
    agendas = Agenda.objects.all().order_by('-created_at', '-id')
    sdgs = SustainableDevelopmentGoal.objects.all().order_by('goal_number')
    status_display_map = dict(Project.STATUS_CHOICES)
    statuses = [{"code": code, "label": status_display_map.get(code, code)} for code, _ in Project.STATUS_CHOICES]

    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        goal_number = request.POST.get('goal_number') or '0'
        deadline = request.POST.get('deadline') or ''
        agenda_id = request.POST.get('agenda') or ''
        sdg_ids = request.POST.getlist('sdgs')  # Get multiple SDG IDs
        project_status = request.POST.get('project_status') or ''

        errors = {}
        if not title:
            errors['title'] = 'Title is required.'
        try:
            goal_number_int = int(goal_number)
            if goal_number_int <= 0:
                errors['goal_number'] = 'Enter a positive number.'
        except Exception:
            errors['goal_number'] = 'Enter a valid number.'
        if not deadline:
            errors['deadline'] = 'Deadline is required.'

        if not errors:
            from django.utils.dateparse import parse_date
            goal.title = title
            goal.target_value = goal_number_int
            goal.target_date = parse_date(deadline)
            goal.agenda_id = int(agenda_id) if agenda_id.isdigit() else None
            goal.project_status = None if not project_status or project_status == 'all' else project_status
            goal.save()
            
            # Set multiple SDGs
            if sdg_ids:
                valid_sdg_ids = [int(sid) for sid in sdg_ids if sid.isdigit()]
                try:
                    goal.sdgs.set(valid_sdg_ids)
                except Exception:
                    # Fallback if migration hasn't been run yet
                    if valid_sdg_ids:
                        goal.sdg_id = valid_sdg_ids[0]
                        goal.save()
            else:
                try:
                    goal.sdgs.clear()
                except Exception:
                    goal.sdg_id = None
                    goal.save()
            
            return redirect('goal')

        return render(request, 'goals/edit_goal.html', {
            'goal': goal,
            'agendas': agendas,
            'sdgs': sdgs,
            'statuses': statuses,
            'errors': errors,
            'form': {
                'title': title,
                'goal_number': goal_number,
                'deadline': deadline,
                'agenda': agenda_id,
                'sdgs': sdg_ids,
                'project_status': project_status,
            },
        })

    # Get selected SDG IDs for the template
    try:
        selected_sdg_ids = list(goal.sdgs.values_list('id', flat=True))
    except Exception:
        # Fallback if migration hasn't been run yet
        selected_sdg_ids = [goal.sdg_id] if goal.sdg_id else []
    
    return render(request, 'goals/edit_goal.html', {
        'goal': goal,
        'agendas': agendas,
        'sdgs': sdgs,
        'statuses': statuses,
        'selected_sdg_ids': selected_sdg_ids,
    })
