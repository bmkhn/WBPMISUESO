from django.shortcuts import render


def analytics_view(request):
    return render(request, 'analytics/analytics.html')