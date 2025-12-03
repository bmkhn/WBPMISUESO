from django.urls import path
from . import views

# Add an app_name for namespacing your URLs
app_name = 'system_settings'

urlpatterns = [
    # Main settings page
    path('', views.settings_view, name='settings'),
    path('api/docs/', views.api_docs, name='api_docs'),
    
    # College CRUD
    path('colleges/', views.manage_colleges, name='manage_colleges'),
    path('colleges/add/', views.add_college, name='add_college'),
    path('colleges/edit/<int:pk>/', views.edit_college, name='edit_college'),
    path('colleges/delete/<int:pk>/', views.delete_college, name='delete_college'),

    # CAMPUS CRUD
    path('campus/', views.manage_campus, name='manage_campus'),
    path('campus/add/', views.add_campus, name='add_campus'),
    path('campus/edit/<int:pk>/', views.edit_campus, name='edit_campus'),
    path('campus/delete/<int:pk>/', views.delete_campus, name='delete_campus'),
    
    # SDG CRUD
    path('sdgs/', views.manage_sdgs, name='manage_sdgs'),
    path('sdgs/add/', views.add_sdg, name='add_sdg'),
    path('sdgs/edit/<int:pk>/', views.edit_sdg, name='edit_sdg'),
    path('sdgs/delete/<int:pk>/', views.delete_sdg, name='delete_sdg'),

    # Project Type CRUD
    path('project-types/', views.manage_project_types, name='manage_project_types'),
    path('project-types/add/', views.add_project_type, name='add_project_type'),
    path('project-types/edit/<int:pk>/', views.edit_project_type, name='edit_project_type'),
    path('project-types/delete/<int:pk>/', views.delete_project_type, name='delete_project_type'),
    
    # System Settings (Key-Value)
    path('system/', views.manage_system_settings, name='manage_system_settings'),
    
    # User Account
    path('account/delete/', views.delete_account, name='delete_account'),

    # API Key Management
    path('api/request/', views.request_api_access, name='request_api_access'),
    path('api/approve/<int:pk>/', views.approve_api_access, name='approve_api_access'),
    path('api/reject/<int:pk>/', views.reject_api_access, name='reject_api_access'),
    path('api/disconnect/<int:pk>/', views.disconnect_api_access, name='disconnect_api_access'),
    path('api/delete/<int:pk>/', views.delete_api_connection, name='delete_api_connection'),

    path('export-data/', views.export_user_data, name='export_user_data'),
]