# shared/archive/views.py (MODIFIED - Simplified Controllers)

from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination # Added pagination support

from .serializers import ProjectSerializer
from .services import ArchiveService # <-- NEW Service Import


class CustomPagination(PageNumberPagination):
    """Standard pagination class for API list views."""
    page_size = 10  # Set default page size
    page_size_query_param = 'page_size'
    max_page_size = 100


# --- Main Render View ---
class ArchiveView(View):
    def get(self, request):
        user_role = getattr(request.user, 'role', None)
        
        if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
            base_template = "base_internal.html"
        else:
            base_template = "base_public.html"

        # Define the categories for the dropdown
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
        }
        
        return render(request, 'archive/archive.html', context)

# --- API Aggregation View ---
class ProjectAggregationAPIView(APIView):
    """Calls the service layer for project aggregation data (for cards)."""
    def get(self, request, category):
        try:
            # Delegate all logic to the Service Layer
            results = ArchiveService.get_aggregated_projects(category=category)
            return Response(results)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        except Exception:
            return Response({"error": "A server error occurred during aggregation."}, status=500)


# --- API Project List View ---
class ProjectListAPIView(ListAPIView):
    """Calls the service layer for detailed project lists (for tables)."""
    serializer_class = ProjectSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        category = self.kwargs.get('category')
        filter_value = self.kwargs.get('filter_value')
        
        # Get query parameters for searching and sorting
        search_params = self.request.query_params
        
        # Delegate all query building and filtering logic to the Service Layer
        queryset = ArchiveService.get_project_list(
            category=category,
            filter_value=filter_value,
            search_params=search_params
        )
        return queryset