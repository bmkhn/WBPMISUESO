from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from system.users.decorators import role_required
from system.users.models import College, User
from .ai_team_generator import get_team_generator
import json


@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"], require_confirmed=True)
def experts_view(request):
    from django.core.paginator import Paginator

    # Get filter options for the modal
    campuses = User.Campus.choices
    colleges = College.objects.all()
    
    from shared.projects.models import Project
    from django.db.models import Q, Count

    # Get all experts and annotate with completed projects count
    experts = User.objects.filter(is_expert=True, is_confirmed=True).select_related('college')
    
    # Apply search filter
    search_query = request.GET.get('search', '').strip()
    if search_query:
        experts = experts.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(middle_name__icontains=search_query)
        )
    
    # Apply campus filter
    campus_filter = request.GET.get('campus', '').strip()
    if campus_filter:
        experts = experts.filter(campus=campus_filter)
    
    # Apply college filter
    college_filter = request.GET.get('college', '').strip()
    if college_filter:
        try:
            college_id = int(college_filter)
            experts = experts.filter(college_id=college_id)
        except ValueError:
            pass
    
    # Annotate each expert with completed_projects count
    # Count projects where user is leader with COMPLETED status
    # Plus count projects where user is provider with COMPLETED status
    experts = experts.annotate(
        led_completed=Count('led_projects', filter=Q(led_projects__status='COMPLETED'), distinct=True),
        member_completed=Count('member_projects', filter=Q(member_projects__status='COMPLETED'), distinct=True)
    )
    
    # Apply sorting
    sort_by = request.GET.get('sort_by', 'name')  # name, projects, campus, college
    order = request.GET.get('order', 'asc')  # asc or desc
    
    if sort_by == 'name':
        if order == 'desc':
            experts = experts.order_by('-last_name', '-first_name')
        else:
            experts = experts.order_by('last_name', 'first_name')
    elif sort_by == 'projects':
        # For sorting by projects, we need to add the counts first, then sort
        # We'll use a custom ordering based on the sum of led and member completed
        experts = list(experts)
        experts.sort(key=lambda x: x.led_completed + x.member_completed, reverse=(order == 'desc'))
        # Convert back to queryset-like list for pagination
        from django.core.paginator import Paginator
        page_number = request.GET.get('page', 1)
        paginator = Paginator(experts, 6)
        page_obj = paginator.get_page(page_number)
        
        # Calculate page range
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
        
        return render(request, 'experts/experts.html', {
            'campuses': campuses,
            'colleges': colleges,
            'experts': page_obj,
            'paginator': paginator,
            'page_obj': page_obj,
            'page_range': page_range,
            'search_query': search_query,
            'campus_filter': campus_filter,
            'college_filter': college_filter,
            'sort_by': sort_by,
            'order': order,
        })
    elif sort_by == 'campus':
        if order == 'desc':
            experts = experts.order_by('-campus', 'last_name', 'first_name')
        else:
            experts = experts.order_by('campus', 'last_name', 'first_name')
    elif sort_by == 'college':
        if order == 'desc':
            experts = experts.order_by('-college__name', 'last_name', 'first_name')
        else:
            experts = experts.order_by('college__name', 'last_name', 'first_name')
    else:
        experts = experts.order_by('last_name', 'first_name')

    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(experts, 6)  # 6 items per page for grid view (3x2)
    page_obj = paginator.get_page(page_number)
    
    # Calculate page range for pagination UI
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
    
    return render(request, 'experts/experts.html', {
        'campuses': campuses,
        'colleges': colleges,
        'experts': page_obj,
        'paginator': paginator,
        'page_obj': page_obj,
        'page_range': page_range,
        'search_query': search_query,
        'campus_filter': campus_filter,
        'college_filter': college_filter,
        'sort_by': sort_by,
        'order': order,
    })


@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"], require_confirmed=True)
def expert_profile_view(request, user_id):
    from django.shortcuts import get_object_or_404
    from shared.projects.models import Project
    from django.db.models import Q, Count, Avg
    
    # Get the expert user
    expert = get_object_or_404(User, id=user_id, is_expert=True, is_confirmed=True)
    
    # Get projects where the expert is either the leader or a provider
    projects = Project.objects.filter(
        Q(project_leader=expert) | Q(providers=expert)
    ).distinct().select_related(
        'project_leader', 'agenda'
    ).prefetch_related(
        'providers', 'sdgs', 'evaluations'
    ).order_by('-start_date')
    
    # Calculate project statistics
    total_projects = projects.count()
    completed_projects = projects.filter(status='COMPLETED').count()
    ongoing_projects = projects.filter(status='IN_PROGRESS').count()
    
    # Calculate average rating from project evaluations
    avg_rating = 0
    evaluation_count = 0
    for project in projects:
        project_evals = project.evaluations.all()
        if project_evals.exists():
            for eval in project_evals:
                avg_rating += eval.rating
                evaluation_count += 1
    
    if evaluation_count > 0:
        avg_rating = avg_rating / evaluation_count
    
    # Get campus display name
    campus_display = dict(User.Campus.choices).get(expert.campus, expert.campus) if expert.campus else "N/A"
    
    # Get college name and logo
    college_name = expert.college.name if expert.college else "N/A"
    college_logo = expert.college.logo.url if expert.college and expert.college.logo else None
    
    return render(request, 'experts/experts_profile.html', {
        'expert': expert,
        'campus_display': campus_display,
        'college_name': college_name,
        'college_logo': college_logo,
        'projects': projects,
        'total_projects': total_projects,
        'completed_projects': completed_projects,
        'ongoing_projects': ongoing_projects,
        'avg_rating': round(avg_rating, 1),
    })


@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"], require_confirmed=True)
@require_POST
def generate_team_view(request):
    """
    API endpoint to generate AI-powered team recommendations.
    """
    try:
        data = json.loads(request.body)
        
        keywords = data.get('keywords', '').strip()
        campus_filter = data.get('campus', '').strip() or None
        college_filter = data.get('college', '').strip() or None
        num_participants = int(data.get('num_participants', 5))
        
        if not keywords:
            return JsonResponse({
                'success': False,
                'error': 'Keywords are required'
            }, status=400)
        
        if num_participants < 1 or num_participants > 20:
            return JsonResponse({
                'success': False,
                'error': 'Number of participants must be between 1 and 20'
            }, status=400)
        
        # Convert college to int if provided
        if college_filter:
            try:
                college_filter = int(college_filter)
            except ValueError:
                college_filter = None
        
        # Generate team
        generator = get_team_generator()
        team_members = generator.generate_team(
            keywords=keywords,
            campus_filter=campus_filter,
            college_filter=college_filter,
            num_participants=num_participants
        )
        
        # Format response
        results = []
        for member in team_members:
            # Get profile picture URL if available
            profile_pic_url = None
            if member.get('user'):
                user = member['user']
                if user.profile_picture:
                    profile_pic_url = user.profile_picture.url
            
            results.append({
                'id': member['id'],
                'name': member['name'],
                'campus': member['campus'],
                'college': member['college'],
                'degree': member['degree'],
                'expertise': member['expertise'],
                'total_projects': member['total_projects'],
                'ongoing_projects': member['ongoing_projects'],
                'avg_rating': round(member['avg_rating'], 2),
                'semantic_score': round(member['semantic_score'], 3),
                'normalized_rating': round(member['normalized_rating'], 3),
                'availability_score': round(member['availability_score'], 3),
                'final_score': round(member['final_score'], 3),
                'profile_picture': profile_pic_url,
            })
        
        return JsonResponse({
            'success': True,
            'team_members': results,
            'count': len(results)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)