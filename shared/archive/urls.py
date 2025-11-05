from django.urls import path
from .views import ArchiveView, ProjectAggregationAPIView, ProjectListAPIView

urlpatterns = [

    path('', ArchiveView.as_view(), name='archive'),
    path('api/aggregate/<str:category>/', ProjectAggregationAPIView.as_view(), name='api_archive_aggregate'),
    path('api/projects/<str:category>/<str:filter_value>/', ProjectListAPIView.as_view(), name='api_archive_list'),
]