from django.urls import path
from .views import agenda_view

urlpatterns = [
    path('', agenda_view, name='agenda'),
]