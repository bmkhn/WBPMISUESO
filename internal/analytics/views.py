from django.shortcuts import render

# --- Main Dashboard View ---
def home_view(request):
    """Renders the main dashboard HTML template."""
    return render(request, 'analytics.html')

# Note: All other chart/metric data views are now handled in api_views.py