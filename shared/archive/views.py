from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination

from django.db.models import Q, Count, F
from django.db.models.functions import ExtractYear
from shared.projects.models import Project
from system.users.models import User
from rest_framework.permissions import AllowAny

from .serializers import ProjectSerializer


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
    user = request.user
    user_role = getattr(user, 'role', None)

    # 1. UESO, Director, VP: See everything
    if user_role in [User.Role.UESO, User.Role.DIRECTOR, User.Role.VP]:
        return Project.objects.all()

    # 2. Faculty, Program Head, Coordinator, Dean:
    if user_role in [User.Role.FACULTY, User.Role.PROGRAM_HEAD, User.Role.COORDINATOR, User.Role.DEAN]:
        college_query = Q()
        if user.college:
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
    permission_classes = [AllowAny]
    def get(self, request, category):
        try:
            base_queryset = _get_role_based_archive_queryset(request)

            field_map = {
                'start_year': 'start_year',
                'estimated_end_date': 'end_year',
                'agenda': 'agenda__name',
                'project_type': 'project_type',
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
                count=Count('id')
            ).order_by(f'-{group_by_field}').values(
                'count', label=F(group_by_field)
            )

            # Format for the frontend
            formatted_results = []
            for item in results:
                label = item['label']
                if not label:
                    label = 'N/A'
 
                if category == 'project_type' and label != 'N/A':
                    label = label.replace('_', ' ').title()

                formatted_results.append({'label': label, 'count': item['count']})
            
            return Response(formatted_results)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": "A server error occurred during aggregation."}, status=500)


# --- API Project List View ---
class ProjectListAPIView(ListAPIView):
    """Calls the service layer for detailed project lists (for tables)."""
    serializer_class = ProjectSerializer
    pagination_class = CustomPagination
    permission_classes = [AllowAny]

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
                    filter_db_value = filter_value.replace(' ', '_').upper()
                    queryset = queryset.filter(project_type=filter_db_value)
                elif category == 'college':
                    queryset = queryset.filter(project_leader__college__name=filter_value)

        # Apply search query
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(project_leader__given_name__icontains=search_query) |
                Q(project_leader__last_name__icontains=search_query) |
                Q(primary_location__icontains=search_query)
            )

        # Apply sorting
        sort_field_map = {
            'title': 'title',
            'start_date': 'start_date',
            'end_date': 'estimated_end_date',
        }
        sort_field = sort_field_map.get(sort_by, 'title') 
        
        if order == 'desc':
            sort_field = f'-{sort_field}'
        
        queryset = queryset.order_by(sort_field)

        return queryset.distinct()