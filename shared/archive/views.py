from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination

from django.db.models import Q, Count, F
from django.db.models.functions import ExtractYear
from shared.projects.models import Project, ProjectType
from system.users.models import User
from rest_framework.permissions import AllowAny
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from system.api.permissions import TieredAPIPermission

from .serializers import ProjectSerializer
from .serializers import ProjectAggregationSerializer
#YML
from rest_framework.decorators import permission_classes
from drf_spectacular.utils import extend_schema

class CustomPagination(PageNumberPagination):
    """Standard pagination class for API list views."""
    page_size = 10 
    page_size_query_param = 'page_size'
    max_page_size = 100


def _get_role_based_archive_queryset(request):
    """
    Returns a base Project queryset filtered based on the user's role
    per the specified business logic.

    LOGIC:
    1. UESO, Director, VP: See EVERYTHING.
    2. Faculty, Program Head, Coordinator, Dean: See ALL COMPLETED projects
       PLUS all IN_PROGRESS projects from their own college.
    3. All others (Guest, Client, Implementer): See ONLY COMPLETED projects.
    """
    user = getattr(request, 'user', None)
    user_role = getattr(user, 'role', None) if user and hasattr(user, 'role') else None

    # If not authenticated or no role, treat as public/guest
    if not user or not getattr(user, 'is_authenticated', False) or not user_role:
        return Project.objects.filter(status="COMPLETED")

    # 1. UESO, Director, VP: See everything
    if user_role in [User.Role.UESO, User.Role.DIRECTOR, User.Role.VP]:
        return Project.objects.all()

    # 2. Faculty, Program Head, Coordinator, Dean:
    if user_role in [User.Role.FACULTY, User.Role.PROGRAM_HEAD, User.Role.COORDINATOR, User.Role.DEAN]:
        college_query = Q()
        if getattr(user, 'college', None):
            college_query = Q(status="IN_PROGRESS") & Q(project_leader__college=user.college)

        return Project.objects.filter(
            Q(status="COMPLETED") | college_query
        ).distinct()

    return Project.objects.filter(status="COMPLETED")


# --- Main Render View ---
class ArchiveView(View):
    def get(self, request):
        user_role = getattr(request.user, 'role', None)
        
        if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
            base_template = "base_internal.html"
        else:
            base_template = "base_public.html"

        categories = [
            ('start_year', 'Year Started'),
            ('estimated_end_date', 'Year Ended'),
            ('agenda', 'Agenda'),
            ('project_type', 'Project Type'),
            ('college', 'College/CORD'),
        ]

        context = {
            'base_template': base_template,
            'categories': categories,
            'default_category': 'start_year',
            'user_role': user_role, 
        }
        
        return render(request, 'archive/archive.html', context)

# --- API Aggregation View ---
class ProjectAggregationAPIView(APIView):
    """Calls the service layer for project aggregation data (for cards)."""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, TieredAPIPermission]
    
    @extend_schema(responses={200: ProjectAggregationSerializer})
    def get(self, request, category):
        try:
            base_queryset = _get_role_based_archive_queryset(request)
            
            # Apply search query if present
            search_query = request.query_params.get('search', None)
            if search_query:
                base_queryset = base_queryset.filter(
                    Q(title__icontains=search_query)
                    | Q(project_leader__given_name__icontains=search_query)
                    | Q(project_leader__last_name__icontains=search_query)
                    | Q(project_leader__username__icontains=search_query)
                    | Q(providers__given_name__icontains=search_query)
                    | Q(providers__last_name__icontains=search_query)
                    | Q(providers__username__icontains=search_query)
                    | Q(primary_location__icontains=search_query)
                ).distinct()

            field_map = {
                'start_year': 'start_year',
                'estimated_end_date': 'end_year',
                'agenda': 'agenda__name',
                'project_type': 'project_type__name',
                'college': 'project_leader__college__name',
            }

            if category not in field_map:
                raise ValueError("Invalid category specified.")

            group_by_field = field_map[category]

            if category == 'start_year':
                base_queryset = base_queryset.annotate(start_year=ExtractYear('start_date'))
            elif category == 'estimated_end_date':
                base_queryset = base_queryset.annotate(end_year=ExtractYear('estimated_end_date'))

            results = base_queryset.values(group_by_field).annotate(
                count=Count('id', distinct=True)
            ).order_by(f'-{group_by_field}').values(
                'count', label=F(group_by_field)
            )

            # Format for the frontend
            formatted_results = []
            for item in results:
                label = item['label']
                if not label:
                    label = 'N/A'
 
                # FIX 2: Removed the .replace() logic because label is now already a clean name string
                
                formatted_results.append({'label': label, 'count': item['count']})
            
            return Response(formatted_results)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            print(f"Aggregation Error: {e}") # Helpful for debugging
            return Response({"error": "A server error occurred during aggregation."}, status=500)


# --- API Project List View ---
class ProjectListAPIView(ListAPIView):
    """Calls the service layer for detailed project lists (for tables)."""

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, TieredAPIPermission]
    serializer_class = ProjectSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        category = self.kwargs.get('category')
        filter_value = self.kwargs.get('filter_value')
        
        # Get query parameters for searching and sorting
        search_params = self.request.query_params
        search_query = search_params.get('search', None)
        sort_by = search_params.get('sort_by', 'title') 
        order = search_params.get('order', 'asc')
        
        queryset = _get_role_based_archive_queryset(self.request)

        if category and filter_value:
            if filter_value == 'N/A':
                if category == 'agenda':
                    queryset = queryset.filter(agenda__name__isnull=True)
                elif category == 'college':
                    queryset = queryset.filter(project_leader__college__name__isnull=True)
                elif category == 'start_year':
                     queryset = queryset.filter(start_date__year__isnull=True)
                elif category == 'estimated_end_date':
                    queryset = queryset.filter(estimated_end_date__year__isnull=True)
                elif category == 'project_type':
                     queryset = queryset.filter(project_type__isnull=True)
            else:
                if category == 'start_year':
                    queryset = queryset.filter(start_date__year=filter_value)
                elif category == 'estimated_end_date':
                    queryset = queryset.filter(estimated_end_date__year=filter_value)
                elif category == 'agenda':
                    queryset = queryset.filter(agenda__name=filter_value)
                elif category == 'project_type':
                    # Filter by Name matches the Aggregation label
                    queryset = queryset.filter(project_type__name=filter_value)
                elif category == 'college':
                    queryset = queryset.filter(project_leader__college__name=filter_value)

        # Apply search query
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(project_leader__given_name__icontains=search_query)
                | Q(project_leader__last_name__icontains=search_query)
                | Q(project_leader__username__icontains=search_query)
                | Q(providers__given_name__icontains=search_query)
                | Q(providers__last_name__icontains=search_query)
                | Q(providers__username__icontains=search_query)
                | Q(primary_location__icontains=search_query)
            )

        # Apply sorting
        sort_field_map = {
            'title': 'title',
            'start_date': 'start_date',
            'end_date': 'estimated_end_date',
            'project_type': 'project_type__name',
            'project_leader__last_name': 'project_leader__last_name',
            'status': 'status',
        }
        sort_field = sort_field_map.get(sort_by, 'title') 
        
        if order == 'desc':
            sort_field = f'-{sort_field}'
        
        queryset = queryset.order_by(sort_field)

        return queryset.distinct()