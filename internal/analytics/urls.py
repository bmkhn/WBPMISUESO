from django.urls import path
from . import views
from . import api_views 

urlpatterns = [
    path('', views.analytics_view, name='analytics'),

    # 2. CARD METRIC DATA VIEWS (Mapped to API Views)
    path('data/metric/projects/', api_views.projects_metric_api, name='projects_metric_data'),
    path('data/metric/events/', api_views.events_metric_api, name='events_metric_data'),
    path('data/metric/providers/', api_views.providers_metric_api, name='providers_metric_data'),
    path('data/metric/individuals/', api_views.individuals_metric_api, name='individuals_metric_data'),

    # 3. CHART DATA VIEWS (Mapped to API Views)
    path('data/chart/active/', api_views.active_projects_chart_api, name='active_projects_chart_data'),
    path('data/chart/budget/', api_views.budget_allocation_chart_api, name='budget_allocation_chart_data'),
    path('data/chart/agenda/', api_views.agenda_distribution_chart_api, name='agenda_distribution_chart_data'),
    path('data/chart/trained/', api_views.trained_individuals_chart_api, name='trained_individuals_chart_data'),
    path('data/chart/requests/', api_views.request_status_chart_api, name='request_status_chart_data'),
    
    path('data/trends/projects/', api_views.project_trends_api, name='project_trends_data'),
]