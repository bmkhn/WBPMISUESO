from django.urls import path
from .views import calendar_view, add_event, events_json, edit_event, delete_event

urlpatterns = [
    path('', calendar_view, name='calendar'),
    path('add_event/', add_event, name='add_event'),
    path('events_json/', events_json, name='events_json'),
    path('edit_event/', edit_event, name='edit_event'),
    path('delete_event/<int:event_id>/', delete_event, name='delete_event'),
]
