from django.urls import path
from . import views

urlpatterns = [
    path('', views.budget_view, name='budget_dashboard'), 
    path('edit/', views.edit_budget_view, name='budget_edit'),
    path('history/', views.budget_history_view, name='budget_history'),
    path('external_sponsors/', views.external_sponsors_view, name='budget_sponsors'),
    path('setup/annual/', views.setup_annual_budget, name='budget_setup'),
    path('export/', views.export_budget_data_view, name='budget_export'),
    path('college/<int:college_id>/projects/', views.view_college_projects, name='college_projects'),
]