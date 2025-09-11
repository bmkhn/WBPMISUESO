from django.urls import path
from .views import announcement_admin_view, add_announcement_view

urlpatterns = [
    path('', announcement_admin_view, name='announcement_admin'),                 # Announcement Admin
    path('add/', add_announcement_view, name='announcement_add'),                # Add Announcement
    # path('edit/<int:id>/', announcement_form_view, name='announcement_edit'),     # Edit Announcement
] 