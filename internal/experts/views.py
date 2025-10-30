from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from system.users.decorators import role_required
from system.users.decorators import role_required
from system.users.models import College, User
from .ai_team_generator import get_team_generator
import json


def get_templates(request):
    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"
    return base_template


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
    
    # Filter to only show experts with at least 1 completed project
    # We need to filter after annotation
    experts = [e for e in experts if (e.led_completed + e.member_completed) >= 1]
    
    # Apply sorting (experts is now a list, not a queryset)
    sort_by = request.GET.get('sort_by', 'name')  # name, projects, campus, college
    order = request.GET.get('order', 'asc')  # asc or desc
    
    if sort_by == 'name':
        experts.sort(key=lambda x: (x.last_name, x.given_name), reverse=(order == 'desc'))
    elif sort_by == 'projects':
        experts.sort(key=lambda x: x.led_completed + x.member_completed, reverse=(order == 'desc'))
    elif sort_by == 'campus':
        experts.sort(key=lambda x: (x.campus or '', x.last_name, x.given_name), reverse=(order == 'desc'))
    elif sort_by == 'college':
        experts.sort(key=lambda x: (x.college.name if x.college else '', x.last_name, x.given_name), reverse=(order == 'desc'))
    else:
        experts.sort(key=lambda x: (x.last_name, x.given_name), reverse=(order == 'desc'))

    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(experts, 12)  
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
    
    # Check if user can create projects (UESO, DIRECTOR, VP only)
    can_create_projects = request.user.role in ['UESO', 'DIRECTOR', 'VP']
    
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
        'can_create_projects': can_create_projects,
    })


def can_view_project(user, project):
    """
    Check if a user can view a project based on visibility restrictions:
    - Non-authenticated users: only COMPLETED projects
    - Project leader/providers: can see their projects regardless of status
    - Dean/Coordinator/Program Head: can see all projects from their college
    - UESO/Director/VP: can see everything
    """
    # UESO, Director, VP can see everything
    if user.is_authenticated and hasattr(user, 'role'):
        if user.role in ["UESO", "DIRECTOR", "VP"]:
            return True
        
        # Project leader or provider can see their own projects
        if project.project_leader == user or user in project.providers.all():
            return True
        
        # Dean, Coordinator, Program Head can see all projects from their college
        if user.role in ["DEAN", "COORDINATOR", "PROGRAM_HEAD"]:
            if user.college and project.project_leader.college == user.college:
                return True
    
    # Non-authenticated or other users can only see COMPLETED projects
    return project.status == 'COMPLETED'


@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"], require_confirmed=True)
def expert_profile_view(request, user_id):
    base_template = get_templates(request)
    from django.shortcuts import get_object_or_404
    from shared.projects.models import Project
    from django.db.models import Q
    
    # Get the expert user
    expert = get_object_or_404(User, id=user_id, is_expert=True, is_confirmed=True)
    
    # Get campus display name
    campus_display = dict(User.Campus.choices).get(expert.campus, expert.campus) if expert.campus else "N/A"
    
    # Get college name and logo
    college_name = expert.college.name if expert.college else "N/A"
    college_logo = expert.college.logo.url if expert.college and expert.college.logo else None
    
    # Get content items - projects where the expert is leader or provider
    # Then apply visibility filtering based on what the VIEWING user can see
    all_projects = Project.objects.filter(
        Q(project_leader=expert) | Q(providers=expert)
    ).distinct().select_related(
        'project_leader', 'agenda'
    ).prefetch_related(
        'providers', 'sdgs'
    ).order_by('-start_date')
    
    # Filter projects based on what the VIEWING user can see
    content_items = [p for p in all_projects if can_view_project(request.user, p)]
    
    # Determine role constants for display
    HAS_COLLEGE_CAMPUS = ["FACULTY", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]
    HAS_DEGREE_EXPERTISE = ["FACULTY", "IMPLEMENTER"]
    HAS_COMPANY_INDUSTRY = ["CLIENT"]
    
    return render(request, 'experts/experts_profile.html', {
        'profile_user': expert,  # Using profile_user to match the template
        'can_edit': False,  # Experts profiles are view-only for others
        'campus_display': campus_display,
        'college_name': college_name,
        'college_logo': college_logo,
        'content_items': content_items,
        'content_items_count': len(content_items),
        'base_template': base_template,
        'HAS_COLLEGE_CAMPUS': HAS_COLLEGE_CAMPUS,
        'HAS_DEGREE_EXPERTISE': HAS_DEGREE_EXPERTISE,
        'HAS_COMPANY_INDUSTRY': HAS_COMPANY_INDUSTRY,
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