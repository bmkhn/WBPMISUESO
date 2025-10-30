from django.shortcuts import render

# --- Main Dashboard View ---
def analytics_view(request):
    """Renders the main dashboard HTML template."""
    return render(request, 'analytics.html')

