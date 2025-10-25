# internal/experts/services.py

from system.users.models import User, College
from django.db.models import Count, Q, Case, When
from typing import List, Dict, Any

from .ai_team_gen_stub import generate_teams_by_ai 


class ExpertService:
    """Service layer for managing Internal Experts and AI Team Generation."""

    BASE_EXPERT_FILTER = Q(role__in=[User.Role.FACULTY, User.Role.IMPLEMENTER]) & Q(is_expert=True)
    TINUIGIBAN_CAMPUS = User.Campus.TINUIGIBAN 

    @staticmethod
    def get_dropdown_options() -> list:
        """
        Retrieves a list of Colleges/CORDs and adds the 'All Experts' option for the dropdown.
        """
        # Start with the 'All Experts' option (filter_key='all')
        options = [{
            'id': 'all',
            'name': 'All Experts',
            'filter_key': 'all',
            'is_default': True
        }]
        
        # Add all colleges that have at least one assigned expert
        college_qs = College.objects.filter(
            user__is_expert=True, user__role__in=[User.Role.FACULTY, User.Role.IMPLEMENTER]
        ).annotate(
            expert_count=Count('user', distinct=True)
        ).order_by('name')

        for college in college_qs:
            options.append({
                'id': str(college.id),
                'name': college.name,
                'filter_key': str(college.id),
                'count': college.expert_count,
                'is_default': False
            })
            
        return options


    @staticmethod
    def get_expert_list(college_id: str, search_params: dict):
        """
        Retrieves the detailed list of experts, filtered by College/CORD ID or ALL,
        and applies searching and sorting. Implements Tiniguiban priority for 'all'.
        """
        queryset = User.objects.filter(ExpertService.BASE_EXPERT_FILTER).select_related('college').all()
        
        # --- 1. Apply Filtering ---
        if college_id != 'all':
            # Filter by specific College ID
            try:
                college_id = int(college_id)
                queryset = queryset.filter(college__id=college_id)
            except ValueError:
                return User.objects.none() 

        # --- 2. Apply Search (Across names and expertise) ---
        search = search_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(given_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(expertise__icontains=search)
            )

        # --- 3. Apply Sorting ---
        sort_by = search_params.get('sort_by', 'last_name')
        order = search_params.get('order', 'asc')
            
        order_prefix = '-' if order == 'desc' else ''
        allowed_sort_fields = ['last_name', 'college__name', 'expertise', 'role', 'campus']
        if sort_by not in allowed_sort_fields:
            sort_by = 'last_name'

        # Special Sorting for 'All Experts' (Tiniguiban First)
        if college_id == 'all':
            # Case/When to give Tiniguiban Campus experts top priority (priority 0)
            queryset = queryset.annotate(
                is_tiniguiban=Case(
                    When(campus=ExpertService.TINUIGIBAN_CAMPUS, then=0), 
                    default=1, 
                )
            ).order_by('is_tiniguiban', f'{order_prefix}{sort_by}')
        else:
            queryset = queryset.order_by(f'{order_prefix}{sort_by}')

        return queryset

    @staticmethod
    def generate_project_teams(num_members: int, topic: str) -> List[Dict[str, Any]]:
        """
        Generates a single best team by calling the AI model with the topic and member count.
        """
        eligible_users = User.objects.filter(ExpertService.BASE_EXPERT_FILTER).all()
        
        # Delegate to the AI generation logic, passing the required team size
        teams = generate_teams_by_ai(eligible_users, num_members, topic) 
        
        return teams