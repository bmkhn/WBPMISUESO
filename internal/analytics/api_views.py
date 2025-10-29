# testingsite/api_views.py (Refactored)

from django.http import JsonResponse
from datetime import datetime
from . import services # Import the service layer

# --- Utility Function ---
def parse_dates_from_request(request):
    """Parses and validates start_date and end_date from request GET parameters."""
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if not start_date_str or not end_date_str:
        return None, None, JsonResponse({'error': 'Missing date parameters (start_date or end_date).'}, status=400)
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return None, None, JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
    
    return start_date, end_date, None

# ==============================================================================
# CARD METRIC VIEWS (Simple API Endpoints)
# ==============================================================================

def projects_metric_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request)
    if error_response: return error_response
    # Pass both dates as positional arguments (this is correct)
    data = services.get_total_projects_count(start_date, end_date) 
    return JsonResponse(data)

def events_metric_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request)
    if error_response: return error_response
    data = services.get_total_events_count(start_date, end_date)
    return JsonResponse(data)

def providers_metric_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request)
    if error_response: return error_response
    data = services.get_total_providers_count(start_date, end_date)
    return JsonResponse(data)

def individuals_metric_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request)
    if error_response: return error_response
    data = services.get_total_trained_individuals_count(start_date, end_date)
    return JsonResponse(data)

# ==============================================================================
# CHART DATA VIEWS
# ==============================================================================

def active_projects_chart_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request)
    if error_response: return error_response
    data = services.get_active_projects_over_time(start_date, end_date) 
    return JsonResponse(data)

def budget_allocation_chart_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request)
    if error_response: return error_response
    data = services.get_budget_allocation_data(start_date, end_date)
    return JsonResponse(data)

def agenda_distribution_chart_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request)
    if error_response: return error_response
    data = services.get_agenda_distribution_data(start_date, end_date)
    return JsonResponse(data)

def trained_individuals_chart_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request)
    if error_response: return error_response
    data = services.get_trained_individuals_data(start_date, end_date)
    return JsonResponse(data)

def request_status_chart_api(request):
    start_date, end_date, error_response = parse_dates_from_request(request)
    if error_response: return error_response
    data = services.get_request_status_data(start_date, end_date)
    return JsonResponse(data)