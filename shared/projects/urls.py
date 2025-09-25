from django.urls import path
from .views import add_project_view, projects_dispatcher
from .views import project_details

urlpatterns = [
    path('', projects_dispatcher, name='project_dispatcher'),       # Project Dispatcher
    path('add/', add_project_view, name='add_project'),             # Add Project
    path('details/<int:pk>/', project_details, name='project_details'), # Project Details
]