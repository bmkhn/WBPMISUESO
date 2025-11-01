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

# ==============================================================================
# CARD METRIC VIEWS (Now use aware datetimes)
# ==============================================================================

def projects_metric_api(request):
    # Use default_days=90 consistent with original analytics script
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300) 
    if error_response: return error_response
    data = services.get_total_projects_count(start_date, end_date)
    return JsonResponse(data)

def events_metric_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300)
    if error_response: return error_response
    data = services.get_total_events_count(start_date, end_date)
    return JsonResponse(data)

def providers_metric_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300)
    if error_response: return error_response
    data = services.get_total_providers_count(start_date, end_date)
    return JsonResponse(data)

def individuals_metric_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300)
    if error_response: return error_response
    data = services.get_total_individuals_trained(start_date, end_date)
    return JsonResponse(data)

# ==============================================================================
# CHART DATA VIEWS (Now use aware datetimes)
# ==============================================================================

def active_projects_chart_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300)
    if error_response: return error_response
    data = services.get_active_projects_over_time(start_date, end_date) 
    return JsonResponse(data)

def budget_allocation_chart_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300)
    if error_response: return error_response
    data = services.get_budget_allocation_data(start_date, end_date)
    return JsonResponse(data)

def agenda_distribution_chart_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300)
    if error_response: return error_response
    data = services.get_agenda_distribution_data(start_date, end_date)
    return JsonResponse(data)
 
def trained_individuals_chart_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300)
    if error_response: return error_response
    data = services.get_trained_individuals_data(start_date, end_date)
    return JsonResponse(data)

def request_status_chart_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300)
    if error_response: return error_response
    data = services.get_request_status_distribution(start_date, end_date)
    return JsonResponse(data)
    
def project_trends_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request, default_days=300) # Use default 90 days
    if error_response: return error_response
    data = services.get_project_trends(start_date, end_date)
    return JsonResponse(data)

# internal/analytics/api_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
# This is the permission class from the package
from rest_framework_api_key.permissions import HasAPIKey

from shared.projects.models import Project # Import a model to get data from

@api_view(['GET'])
@permission_classes([HasAPIKey]) # This line is the magic!
def get_public_projects(request):
    """
    An example API endpoint that is protected by an API Key.
    It returns a list of all completed projects.
    """
    try:
        # You can get the APIKey object that was used, if needed
        # api_key = request.auth
        
        projects = Project.objects.filter(status='COMPLETED')
        
        # We serialize the data into a simple dictionary
        data = [
            {
                'title': project.title,
                'status': project.status,
                'start_date': project.start_date,
                'end_date': project.end_date,
            }
            for project in projects
        ]
        
        return Response(data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)