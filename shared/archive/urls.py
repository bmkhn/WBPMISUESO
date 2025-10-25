# shared/archive/urls.py

from django.urls import path
from .views import ArchiveView, ProjectAggregationAPIView, ProjectListAPIView

urlpatterns = [
    # Main archive page view
    path('', ArchiveView.as_view(), name='archive'),
    
    # API endpoints
    # 1. API for fetching aggregated project counts (for the cards)
    path('api/aggregate/<str:category>/', ProjectAggregationAPIView.as_view(), name='api_archive_aggregate'),
    
    # 2. API for fetching the list of projects (for the table)
    path('api/projects/<str:category>/<str:filter_value>/', ProjectListAPIView.as_view(), name='api_archive_list'),
]