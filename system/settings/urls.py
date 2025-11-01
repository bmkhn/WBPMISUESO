from django.urls import path
from . import views

# Add an app_name for namespacing your URLs
app_name = 'system_settings'

urlpatterns = [
    # Main settings page
    path('', views.settings_view, name='settings'),
    
    # College CRUD
    path('colleges/', views.manage_colleges, name='manage_colleges'),
    path('colleges/add/', views.add_college, name='add_college'),
    path('colleges/edit/<int:pk>/', views.edit_college, name='edit_college'),
    path('colleges/delete/<int:pk>/', views.delete_college, name='delete_college'),

    path('campus/', views.manage_campus, name='manage_campus'),
    path('campus/add/', views.add_campus, name='add_campus'),
    path('campus/edit/<int:pk>/', views.edit_campus, name='edit_campus'),
    path('campus/delete/<int:pk>/', views.delete_campus, name='delete_campus'),
    
    # SDG CRUD
    path('sdgs/', views.manage_sdgs, name='manage_sdgs'),
    #
    # THIS IS THE CORRECTED LINE:
    path('sdgs/add/', views.add_sdg, name='add_sdg'),
    #
    path('sdgs/edit/<int:pk>/', views.edit_sdg, name='edit_sdg'),
    path('sdgs/delete/<int:pk>/', views.delete_sdg, name='delete_sdg'),
    
    # System Settings (Key-Value)
    path('system/', views.manage_system_settings, name='manage_system_settings'),
    
    # User Account
    path('account/delete/', views.delete_account, name='delete_account'),

    # API Key Management
    path('api-keys/', views.manage_api_keys, name='manage_api_keys'),
    path('api-keys/add/', views.add_api_key, name='add_api_key'),
    path('api-keys/revoke/<str:pk>/', views.revoke_api_key, name='revoke_api_key'),
]