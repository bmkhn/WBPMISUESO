from django.urls import path
# We rename the views we import
from .views import calendar_view, meeting_event_list, meeting_event_detail

urlpatterns = [
    path('', calendar_view, name='calendar'),
    
    # RESTful API endpoints for meeting events
    # GET, POST /calendar/events/
    path('events/', meeting_event_list, name='meeting_event_list'),
    
    # PUT, DELETE /calendar/events/<int:event_id>/
    path('events/<int:event_id>/', meeting_event_detail, name='meeting_event_detail'),
]