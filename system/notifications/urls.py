from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list, name='notifications'),
    path('mark-as-read/<int:notification_id>/', views.mark_as_read, name='mark_notification_read'),
    path('mark-all-as-read/', views.mark_all_as_read, name='mark_all_notifications_read'),
    path('unread-count/', views.get_unread_count, name='get_unread_count'),
    path('recent/', views.get_recent_notifications, name='get_recent_notifications'),
]
