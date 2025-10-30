from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('api/chart/submission-status/', views.get_submission_status_data, name='submission_status_chart'),
    path('api/chart/project-status/', views.get_project_status_data, name='project_status_chart'),
] 