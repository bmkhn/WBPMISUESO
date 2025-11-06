from django.http import JsonResponse
from datetime import datetime, timedelta # Make sure timedelta is imported
from django.utils import timezone # Import timezone for aware datetimes
from . import services 

# --- Updated Utility Function ---
def parse_dates_from_request(request, default_days=300): # Added default_days
    """
    Parses start_date and end_date from request GET parameters.
    Uses a default range (last 'default_days') if parameters are missing or empty.
    Returns aware datetime objects.
    """
    start_date_str = request.GET.get('start_date') # Changed from start
    end_date_str = request.GET.get('end_date')     # Changed from end
    
    current_tz = timezone.get_current_timezone()
    now = timezone.now()

    # Default end_date is today (end of day)
    default_end_date = now.replace(hour=23, minute=59, second=59)
    # Default start_date is 'default_days' ago (start of day)
    default_start_date = (default_end_date - timedelta(days=default_days)).replace(hour=0, minute=0, second=0)

    try:
        if end_date_str:
            dt = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = timezone.make_aware(dt.replace(hour=23, minute=59, second=59), current_tz)
        else:
            end_date = default_end_date
            
        if start_date_str:
            dt = datetime.strptime(start_date_str, '%Y-%m-%d')
            start_date = timezone.make_aware(dt.replace(hour=0, minute=0, second=0), current_tz)
        else:
            # If start is missing, calculate based on the (potentially non-default) end_date
             start_date = (end_date - timedelta(days=default_days)).replace(hour=0, minute=0, second=0)

        # Basic validation: start date should not be after end date
        if start_date > end_date:
             # Reset to default range if dates are illogical
             start_date = default_start_date
             end_date = default_end_date
             # Optionally return an error instead:
             # return None, None, JsonResponse({'error': 'Start date cannot be after end date.'}, status=400)

    except ValueError:
        return None, None, JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
    
    return start_date, end_date, None # Return aware datetimes

def get_user_college(request):
    """
    Helper function to determine if user should see only their college's data.
    Returns college object if user role is PROGRAM_HEAD, DEAN, or COORDINATOR.
    Returns None for VP, DIRECTOR, UESO (they see all data).
    """
    if hasattr(request.user, 'role') and request.user.role in ['PROGRAM_HEAD', 'DEAN', 'COORDINATOR']:
        return request.user.college
    return None

# ==============================================================================
# CARD METRIC VIEWS (Now use aware datetimes)
# ==============================================================================

def projects_metric_api(request):
    # Use default_days=300 consistent with parse_dates_from_request default
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300) 
    if error_response: return error_response
    # --- MODIFIED: Added try/except block ---
    try:
        user_college = get_user_college(request)
        data = services.get_total_projects_count(start_date, end_date, college=user_college)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'error': 'Internal Server Error while calculating projects metric.', 
            'detail': str(e)
        }, status=500)
    # --- END MODIFIED ---

def events_metric_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300)
    if error_response: return error_response
    # --- MODIFIED: Added try/except block ---
    try:
        user_college = get_user_college(request)
        data = services.get_total_events_count(start_date, end_date, college=user_college)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'error': 'Internal Server Error while calculating events metric.', 
            'detail': str(e)
        }, status=500)
    # --- END MODIFIED ---

def providers_metric_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300)
    if error_response: return error_response
    # --- MODIFIED: Added try/except block ---
    try:
        user_college = get_user_college(request)
        data = services.get_total_providers_count(start_date, end_date, college=user_college)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'error': 'Internal Server Error while calculating providers metric.', 
            'detail': str(e)
        }, status=500)
    # --- END MODIFIED ---

def individuals_metric_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300)
    if error_response: return error_response
    # --- MODIFIED: Added try/except block ---
    try:
        user_college = get_user_college(request)
        data = services.get_total_individuals_trained(start_date, end_date, college=user_college)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'error': 'Internal Server Error while calculating trained individuals metric.', 
            'detail': str(e)
        }, status=500)
    # --- END MODIFIED ---

# ==============================================================================
# CHART DATA VIEWS (Now use aware datetimes)
# ==============================================================================

def active_projects_chart_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300)
    if error_response: return error_response
    # --- MODIFIED: Added try/except block ---
    try:
        user_college = get_user_college(request)
        data = services.get_active_projects_over_time(start_date, end_date, college=user_college) 
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'error': 'Internal Server Error while calculating active projects chart data.', 
            'detail': str(e)
        }, status=500)
    # --- END MODIFIED ---

def budget_allocation_chart_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300)
    if error_response: return error_response
    # --- MODIFIED: Added try/except block ---
    try:
        user_college = get_user_college(request)
        # This now calls the multi-series function in services.py
        data = services.get_budget_allocation_data(start_date, end_date, college=user_college)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'error': 'Internal Server Error while calculating budget allocation chart data.', 
            'detail': str(e)
        }, status=500)
    # --- END MODIFIED ---

def agenda_distribution_chart_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300)
    if error_response: return error_response
    # --- MODIFIED: Added try/except block ---
    try:
        user_college = get_user_college(request)
        data = services.get_agenda_distribution_data(start_date, end_date, college=user_college)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'error': 'Internal Server Error while calculating agenda distribution chart data.', 
            'detail': str(e)
        }, status=500)
    # --- END MODIFIED ---
 
def trained_individuals_chart_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300)
    if error_response: return error_response
    # --- MODIFIED: Added try/except block ---
    try:
        user_college = get_user_college(request)
        data = services.get_trained_individuals_data(start_date, end_date, college=user_college)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'error': 'Internal Server Error while calculating trained individuals chart data.', 
            'detail': str(e)
        }, status=500)
    # --- END MODIFIED ---

def request_status_chart_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300)
    if error_response: return error_response
    # --- MODIFIED: Added try/except block ---
    try:
        user_college = get_user_college(request)
        data = services.get_request_status_distribution(start_date, end_date, college=user_college)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'error': 'Internal Server Error while calculating request status chart data.', 
            'detail': str(e)
        }, status=500)
    # --- END MODIFIED ---
    
def project_trends_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300) # Use default 90 days
    if error_response: return error_response
    # --- MODIFIED: Added try/except block ---
    try:
        user_college = get_user_college(request)
        data = services.get_project_trends(start_date, end_date, college=user_college)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'error': 'Internal Server Error while calculating project trends data.', 
            'detail': str(e)
        }, status=500)
    # --- END MODIFIED ---

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework_api_key.permissions import HasAPIKey

from shared.projects.models import Project 
from .serializers import ProjectReadOnlySerializer  # <-- ADD THIS IMPORT

@api_view(['GET'])
@permission_classes([HasAPIKey]) 
def get_public_projects(request):
    """
    An example API endpoint that is protected by an API Key.
    It returns a list of all completed projects.
    """
    try:
        
        projects = Project.objects.all()

        data = [
            {
                'title': project.title,
                'status': project.status,
                'start_date': project.start_date,
                'end_date': project.estimated_end_date,
            }
            for project in projects
        ]
        
        return Response(data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#
# ----------------- ADD THE NEW VIEW BELOW -----------------
#

@api_view(['GET'])
@permission_classes([HasAPIKey]) 
def get_all_project_data(request):
    """
    A read-only API endpoint that returns ALL data for all projects,
    including nested events, documents, and evaluations.
    """
    try:
        # Get all projects, prefetching related data for efficiency
        projects = Project.objects.prefetch_related(
            'documents', 
            'events', 
            'evaluations', 
            'project_leader', 
            'providers', 
            'agenda', 
            'sdgs'
        ).all()

        # Use the new serializer to package all data
        serializer = ProjectReadOnlySerializer(projects, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)