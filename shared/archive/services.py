from django.db.models import Count
from django.db.models.functions import ExtractYear
from django.db.models import Q

from shared.projects.models import Project, ProjectType
from system.users.models import College
from internal.agenda.models import Agenda


class ArchiveService:
    """
    A service layer class dedicated to handling the complex database queries 
    for project aggregation and listing in the archive.
    """

    # Map: category_slug -> (field_path, type_of_grouping, source_model/choices)
    CATEGORY_MAP = {
        'start_year': ('start_date', 'year', None),
        'estimated_end_date': ('estimated_end_date', 'year', None),
        'agenda': ('agenda', 'fk', Agenda),
        'project_type': ('project_type', 'fk', ProjectType),
        'college': ('project_leader__college', 'fk', College),
    }

    @staticmethod
    def get_aggregated_projects(category: str) -> list:
        """
        Retrieves a list of groups (e.g., years, agendas, colleges) and the 
        count of projects in each group for displaying the category cards.
        """
        if category not in ArchiveService.CATEGORY_MAP:
            raise ValueError(f"Invalid aggregation category: {category}")

        field_path, group_type, source = ArchiveService.CATEGORY_MAP[category]
        
        # 1. Base QuerySet: Filter out null values for the grouping field
        queryset = Project.objects.filter(**{f'{field_path}__isnull': False})
        
        results = []

        if group_type == 'year':
            # Grouping for Dates (Year Started/Ended)
            aggregation_qs = queryset.annotate(
                key=ExtractYear(field_path)
            ).values('key').annotate(
                count=Count('id')
            ).order_by('-key')
            
            for item in aggregation_qs:
                key_value = item.get('key')
                if key_value:
                    results.append({
                        'id': str(key_value),
                        'name': str(key_value),
                        'count': item['count'],
                        'filter_key': str(key_value)
                    })
        
        elif group_type == 'choice':
            # Grouping for Choice Fields (Project Type)
            aggregation_qs = queryset.values(field_path).annotate(
                count=Count('id')
            ).order_by(field_path)
            
            choice_dict = dict(source)
            for item in aggregation_qs:
                field_value = item[field_path]
                results.append({
                    'id': field_value,
                    'name': choice_dict.get(field_value, field_value),
                    'count': item['count'],
                    'filter_key': field_value
                })
        
        elif group_type == 'fk':
            # Grouping for Foreign Keys (Agenda, College, ProjectType)
            
            if source == Agenda:
                source_qs = Agenda.objects.annotate(
                    count=Count('projects')
                ).filter(count__gt=0).order_by('name')

                for item in source_qs:
                    results.append({
                        'id': str(item.id),
                        'name': item.name,
                        'count': item.count,
                        'filter_key': str(item.id)
                    })
            
            elif source == ProjectType:
                # FIX: Added block to handle ProjectType aggregation
                source_qs = ProjectType.objects.annotate(
                    count=Count('projects')
                ).filter(count__gt=0).order_by('name')

                for item in source_qs:
                    results.append({
                        'id': str(item.id),
                        'name': item.name,
                        'count': item.count,
                        # Use name as filter key to match the API View logic
                        'filter_key': item.name 
                    })

            elif source == College:
                # Groups projects by the College of the Project Leader
                source_qs = College.objects.annotate(
                    count=Count('user__led_projects', distinct=True) 
                ).filter(count__gt=0).order_by('name')

                for item in source_qs:
                    results.append({
                        'id': str(item.id),
                        'name': item.name,
                        'count': item.count,
                        'filter_key': str(item.id)
                    })
            
        return results

    @staticmethod
    def get_project_list(category: str, filter_value: str, search_params: dict):
        """
        Retrieves the detailed project list, filtered by a specific group 
        and applies searching and sorting from the request parameters.
        """
        if category not in ArchiveService.CATEGORY_MAP:
            raise ValueError(f"Invalid category for filtering: {category}")
        
        # Pre-select related fields to minimize database queries
        queryset = Project.objects.select_related('project_leader', 'agenda').all()
        
        # --- 1. Apply Filtering ---
        if category == 'start_year':
            queryset = queryset.filter(start_date__year=filter_value)
        elif category == 'estimated_end_date':
            queryset = queryset.filter(estimated_end_date__year=filter_value)
        elif category == 'agenda':
            queryset = queryset.filter(agenda__id=filter_value)
        elif category == 'project_type':
            queryset = queryset.filter(project_type=filter_value)
        elif category == 'college':
            queryset = queryset.filter(project_leader__college__id=filter_value)

        # --- 2. Apply Search (Across title and project leader name) ---
        search = search_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(project_leader__given_name__icontains=search) |
                Q(project_leader__last_name__icontains=search) 
            )

        # --- 3. Apply Sorting ---
        sort_by = search_params.get('sort_by', 'title')
        order = search_params.get('order', 'asc')
            
        order_prefix = '-' if order == 'desc' else ''
        
        # Explicitly defining allowed sort fields for security and correctness
        allowed_sort_fields = [
            'title', 'start_date', 'estimated_end_date', 'status',
            'project_leader__username', 'estimated_trainees'
        ]
        
        if sort_by not in allowed_sort_fields:
            sort_by = 'title'

        queryset = queryset.order_by(f'{order_prefix}{sort_by}')

        return queryset