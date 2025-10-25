# internal/experts/urls.py (MODIFIED)

from django.urls import path
from .views import experts_view, ExpertAggregationAPIView, ExpertListAPIView, TeamGenerationAPIView, ExpertProfileView

urlpatterns = [
    path('', experts_view, name='experts'),
    path('<int:pk>/profile/', ExpertProfileView.as_view(), name='expert_profile'), 
    
    # API endpoint for initial load (uses filter_value='all')
    path('api/aggregate_experts/', ExpertAggregationAPIView.as_view(), name='api_expert_aggregate'),
    
    # API endpoints for Drill-Down (Table/Card view after filter is selected)
    # The 'college_id' is passed as the filter_value segment
    path('api/experts/filter/<str:filter_value>/', ExpertListAPIView.as_view(), name='api_expert_list'),
    
    # API endpoint for AI Team Generation (POST action)
    path('api/generate_teams/', TeamGenerationAPIView.as_view(), name='api_generate_teams'),
]