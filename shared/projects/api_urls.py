from django.urls import path
from rest_framework.routers import DefaultRouter
from . import api_views

# Use as_view() to map HTTP methods to ViewSet actions
expense_list = api_views.ProjectExpenseViewSet.as_view({
    'get': 'list',   # GET /api/projects/{project_pk}/expenses/
    'post': 'create' # POST /api/projects/{project_pk}/expenses/
})

expense_detail = api_views.ProjectExpenseViewSet.as_view({
    'get': 'retrieve', # GET /api/projects/{project_pk}/expenses/{pk}/
    'put': 'update',   # PUT /api/projects/{project_pk}/expenses/{pk}/
    'patch': 'partial_update', # PATCH /api/projects/{project_pk}/expenses/{pk}/
    'delete': 'destroy' # DELETE /api/projects/{project_pk}/expenses/{pk}/
})

urlpatterns = [
    # Route for listing and creating expenses for a specific project
    path('<int:project_pk>/expenses/', expense_list, name='projectexpense-list'),
    
    # Route for retrieving, updating, and deleting a specific expense
    path('<int:project_pk>/expenses/<int:pk>/', expense_detail, name='projectexpense-detail'),
]