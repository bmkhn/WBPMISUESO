from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import DetailView 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q 

from system.users.models import User
from .services import ExpertService 
from .serializers import ExpertSerializer


class CustomPagination(PageNumberPagination):
    """Standard pagination class for API list views."""
    page_size = 12 
    page_size_query_param = 'page_size'
    max_page_size = 100


@login_required
def experts_view(request):
    user_role = getattr(request.user, 'role', None)
    
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"

    # Get the dynamic dropdown options from the service layer
    dropdown_options = ExpertService.get_dropdown_options()

    context = {
        'base_template': base_template,
        'dropdown_options': dropdown_options,
        'can_generate_teams': user_role in [User.Role.DIRECTOR, User.Role.VP]
    }
    
    return render(request, 'experts/experts.html', context)


@method_decorator(login_required, name='dispatch')
class ExpertAggregationAPIView(ListAPIView):
    """
    Used for the initial page load to return the default 'All Experts' list 
    with Tiniguiban priority sorting applied.
    """
    serializer_class = ExpertSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        search_params = self.request.query_params
        
        # Use the 'all' key as the default filter
        queryset = ExpertService.get_expert_list(
            college_id='all',
            search_params=search_params
        )
        return queryset


@method_decorator(login_required, name='dispatch')
class ExpertListAPIView(ListAPIView):
    """Lists detailed expert profiles filtered by the specific college_id."""
    serializer_class = ExpertSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        # The URL pattern uses the filter_value as the college_id/filter_key
        college_id = self.kwargs.get('filter_value') 
        
        if not college_id:
            college_id = 'all'

        search_params = self.request.query_params
        
        queryset = ExpertService.get_expert_list(
            college_id=college_id,
            search_params=search_params
        )
        return queryset


@method_decorator(login_required, name='dispatch')
class TeamGenerationAPIView(APIView):
    """
    API endpoint to trigger the AI-based team generation service.
    Accepts 'topic' and 'num_members'.
    """
    def post(self, request, *args, **kwargs):
        if request.user.role not in [User.Role.DIRECTOR, User.Role.VP]:
             return Response({"error": "Permission denied. Only Directors or VPs can initiate AI team generation."}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            num_members = request.data.get('num_members')
            topic = request.data.get('topic', '').strip() 
            
            try:
                num_members = int(num_members)
            except (ValueError, TypeError):
                return Response({"error": "Invalid value for number of members. Must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
                
            if num_members <= 0:
                 return Response({"error": "Number of members must be positive."}, status=status.HTTP_400_BAD_REQUEST)

            if not topic: 
                 return Response({"error": "Topic/Expertise is required for team generation."}, status=status.HTTP_400_BAD_REQUEST)

            generated_teams = ExpertService.generate_project_teams(num_members=num_members, topic=topic)
            
            if not generated_teams:
                 return Response({"error": f"AI could not generate teams for topic '{topic}'. Check that eligible experts with relevant expertise exist."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(generated_teams, status=status.HTTP_200_OK)
            
        except Exception:
            return Response({"error": "Team generation failed due to an unexpected server error."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(login_required, name='dispatch')
class ExpertProfileView(DetailView):
    """
    Displays the detailed profile for a single expert (User).
    """
    model = User
    template_name = 'experts/experts_profile.html'
    context_object_name = 'expert' 

    def get_queryset(self):
        return User.objects.filter(
            Q(role__in=[User.Role.FACULTY, User.Role.IMPLEMENTER]) & Q(is_expert=True)
        ).select_related('college').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_role = getattr(self.request.user, 'role', None)
        
        if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
            context['base_template'] = "base_internal.html"
        else:
            context['base_template'] = "base_public.html"
            
        return context