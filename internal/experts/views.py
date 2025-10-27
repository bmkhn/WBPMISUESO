from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from system.users.decorators import role_required, user_confirmed
from system.users.models import College, User
from .ai_team_generator import get_team_generator
import json


@user_confirmed
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"])
def experts_view(request):
    from django.core.paginator import Paginator
    
    # Get filter options for the modal
    campuses = User.Campus.choices
    colleges = College.objects.all()
    
    # Get all expert users
    experts = User.objects.filter(is_expert=True, is_confirmed=True).select_related('college').order_by('last_name', 'first_name')
    
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
    })


@user_confirmed
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"])
def expert_profile_view(request):
    return render(request, 'experts/experts_profile.html')  # Add Expert Context Later


@user_confirmed
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"])
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