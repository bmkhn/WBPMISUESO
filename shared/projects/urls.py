from django.urls import path
from .views import add_project_view, projects_dispatcher

urlpatterns = [
    path('', projects_dispatcher, name='project_dispatcher'),       # Project Dispatcher
    path('add/', add_project_view, name='add_project'),             # Add Project
]