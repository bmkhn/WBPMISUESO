from django.urls import path
from .views import calendar_view, meeting_event_list, meeting_event_detail, validate_datetime_conflict

urlpatterns = [
    path('', calendar_view, name='calendar'),
    path('events/', meeting_event_list, name='meeting_event_list'),
    path('events/<int:event_id>/', meeting_event_detail, name='meeting_event_detail'),
    path('validate-datetime/', validate_datetime_conflict, name='calendar_validate_datetime_conflict'),
]