from django.urls import path
from .views import request_dispatcher, submit_request, request_details_dispatcher, admin_request_details_entry, admin_request_action

urlpatterns = [
    path('', request_dispatcher, name='request_dispatcher'),
    path('submit/', submit_request, name='submit_request'),
    path('details/<int:pk>/', request_details_dispatcher, name='request_details_dispatcher'),
    path('admin_entry/<int:pk>/', admin_request_details_entry, name='admin_request_details_entry'),
    path('admin_action/<int:pk>/', admin_request_action, name='admin_request_action'),
]