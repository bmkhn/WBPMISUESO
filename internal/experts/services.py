# pasttimer/visual/Visual-5650bbfce2f4db863a5e0a8090389bdc077dc967/internal/experts/services.py

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
# Assuming User and College models are defined in system.users.models as per existing imports in views.py
from system.users.models import College, User 
from .ai_team_generator import get_team_generator
import json

def get_api_experts_queryset():
    """
    Returns the base queryset for experts to be used by the API (unpaginated).
    """
    # Fetch all confirmed experts, selecting related college for efficiency
    return User.objects.filter(is_expert=True, is_confirmed=True).select_related('college').order_by('last_name', 'first_name')

def get_experts_paginated_context(page_number=1, items_per_page=6):
    """
    Handles fetching and pagination logic for the main experts HTML view.
    """
    # Get filter options for the modal
    campuses = User.Campus.choices
    colleges = College.objects.all()
    
    # Get all expert users (same query as the old view)
    experts = get_api_experts_queryset()
    
    # Pagination
    paginator = Paginator(experts, items_per_page)
    page_obj = paginator.get_page(page_number)
    
    # Calculate page range for pagination UI (copied logic from old view)
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
        
    return {
        'campuses': campuses,
        'colleges': colleges,
        'experts': page_obj,
        'paginator': paginator,
        'page_obj': page_obj,
        'page_range': page_range,
    }

def get_expert_by_id(user_id):
    """
    Retrieves a single expert user by ID for the dynamic profile page.
    """
    return get_object_or_404(User.objects.select_related('college'), id=user_id, is_expert=True, is_confirmed=True)


def generate_team_recommendations(keywords, campus_filter, college_filter, num_participants):
    """
    Contains the core logic for the AI-powered team generation (pulled from old views.py).
    """
    if not keywords:
        raise ValueError('Keywords are required')
    
    if num_participants < 1 or num_participants > 20:
        raise ValueError('Number of participants must be between 1 and 20')
    
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
    
    # Format response (copied logic from old views.py)
    results = []
    for member in team_members:
        profile_pic_url = None
        if member.get('user') and member['user'].profile_picture:
            profile_pic_url = member['user'].profile_picture.url
        
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
    
    return results