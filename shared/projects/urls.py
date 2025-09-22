from django.urls import path
from .views import add_project_view

urlpatterns = [
    
    path('add/', add_project_view, name='add_project'),  # Add Project
]