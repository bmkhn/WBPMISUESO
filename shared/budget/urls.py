from django.urls import path
from . import views

urlpatterns = [
    # 1. Main Dashboard (Renders 'budget.html' dynamically)
    path('', views.budget_view, name='budget_dashboard'), 

    # 2. Edit Page (Renders 'edit_budget.html' dynamically)
    path('edit/', views.edit_budget_view, name='budget_edit'),
    
    # 3. History Page (Renders 'history.html')
    path('history/', views.budget_history_view, name='budget_history'),

    # 4. External Sponsors Page (Renders 'external_sponsors.html')
    path('external_sponsors/', views.external_sponsors_view, name='budget_sponsors'),
    
    # 5. Setup (For first-time admin setup)
    path('setup/annual/', views.setup_annual_budget, name='budget_setup'),
]