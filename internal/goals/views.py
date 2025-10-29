from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.utils.dateparse import parse_date
from system.users.decorators import role_required
from .models import Goal, GoalQualifier
# Forms are no longer used; the page uses JSON API endpoints

@role_required(allowed_roles=["DIRECTOR", "VP", "UESO"])
def goal_view(request):
    # Simple view that just renders the static template
    return render(request, 'goals/goals.html')

    


# -----------------------------
# JSON API for dynamic frontend
# -----------------------------

def _serialize_goal(goal: Goal) -> dict:
    """Return a JSON-serializable dict for the Goal expected by the frontend."""
    progress = 0
    try:
        if goal.target_value:
            progress = max(0, min(100, int(round((goal.current_value or 0) * 100 / goal.target_value))))
    except Exception:
        progress = 0

    return {
        'id': goal.id,
        'title': goal.title,
        # Frontend expects these fields; not in model → return defaults
        'agenda': getattr(goal, 'agenda', '') or '',
        'sdg': getattr(goal, 'sdg', '') or '',
        'status': goal.status,
        'goal_number': goal.target_value or 0,
        'deadline': goal.target_date.isoformat() if goal.target_date else None,
        'progress': progress,
    }


@role_required(allowed_roles=["DIRECTOR", "VP", "UESO"])
@require_http_methods(["GET", "POST"])
@csrf_protect
def api_goals(request):
    """GET: list goals; POST: create goal.
    Frontend hits /goals/api/goals/ with JSON body for POST.
    """
    if request.method == 'GET':
        goals = Goal.objects.all().order_by('-created_at')
        return JsonResponse({'success': True, 'goals': [_serialize_goal(g) for g in goals]})

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

    goal.save()
    return JsonResponse({'success': True, 'goal': _serialize_goal(goal)})


@role_required(allowed_roles=["DIRECTOR", "VP", "UESO"])
@require_http_methods(["GET"])
def api_goal_qualifiers(request, goal_id: int):
    """Return qualifiers for a goal in the shape expected by the UI table.
    Our model differs, so we map minimal fields. """
    goal = get_object_or_404(Goal, id=goal_id)
    rows = []
    for q in goal.qualifiers.all().order_by('created_at'):
        rows.append({
            'title': q.name,
            'team_leader': '',  # Not available in current model
            'start_date': (q.completed_at.date().isoformat() if q.completed_at else q.created_at.date().isoformat()),
            'status': 'Completed' if q.is_completed else 'Pending',
        })
    return JsonResponse({'success': True, 'projects': rows})
