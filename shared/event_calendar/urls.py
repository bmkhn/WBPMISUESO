from django.urls import path
from .views import calendar_view, get_events, add_event

urlpatterns = [
    path('', calendar_view, name='calendar'),
    path('events/', get_events, name='get_events'),
    path('event/add/', add_event, name='add_event'),
]
