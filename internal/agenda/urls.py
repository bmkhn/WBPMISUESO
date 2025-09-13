from django.urls import path
from .views import agenda_view, add_agenda_view

urlpatterns = [
    path('', agenda_view, name='agenda'),
    path('add/', add_agenda_view, name='add_agenda'),
]