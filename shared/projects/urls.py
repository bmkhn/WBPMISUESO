from django.urls import path
from .views import (
    add_project_view, projects_dispatcher, project_profile,
    project_overview, project_providers, project_events, project_files, project_submissions, project_expenses, project_evaluations,
    cancel_project, undo_cancel_project,
)

urlpatterns = [
    path('', projects_dispatcher, name='project_dispatcher'),
    path('add/', add_project_view, name='add_project'),

    path('<int:pk>/', project_profile, name='project_profile'),
    path('<int:pk>/overview/', project_overview, name='project_overview'),
    path('<int:pk>/providers/', project_providers, name='project_providers'),
    path('<int:pk>/events/', project_events, name='project_events'),
    path('<int:pk>/files/', project_files, name='project_files'),
    path('<int:pk>/submissions/', project_submissions, name='project_submissions'),
    path('<int:pk>/expenses/', project_expenses, name='project_expenses'),
    path('<int:pk>/evaluations/', project_evaluations, name='project_evaluations'),

    path('<int:pk>/cancel/', cancel_project, name='cancel_project'),
    path('<int:pk>/undo_cancel/', undo_cancel_project, name='undo_cancel_project'),
]