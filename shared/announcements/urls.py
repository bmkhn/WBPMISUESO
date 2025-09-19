from django.urls import path
from .views import add_announcement_view, edit_announcement_view, delete_announcement_view, announcement_dispatch_view, announcement_details_dispatch_view, archive_announcement_view, unarchive_announcement_view

urlpatterns = [
    path('', announcement_dispatch_view, name='announcement_dispatcher'),                         # Role-based Announcement
    path('add/', add_announcement_view, name='announcement_add'),                               # Add Announcement
    path('edit/<int:id>/', edit_announcement_view, name='announcement_edit'),                   # Edit Announcement
    path('delete/<int:id>/', delete_announcement_view, name='announcement_delete'),             # Delete Announcement
    path('details/<int:id>/', announcement_details_dispatch_view, name='announcement_details'), # Admin Announcement Details
    path('archive/<int:id>/', archive_announcement_view, name='announcement_archive'),          # Archive Announcement
    path('unarchive/<int:id>/', unarchive_announcement_view, name='announcement_unarchive'),    # Unarchive Announcement
]