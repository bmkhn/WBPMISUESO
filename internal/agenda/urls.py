from django.urls import path
from .views import agenda_view, add_agenda_view, edit_agenda_view, delete_agenda_view

urlpatterns = [
    path('', agenda_view, name='agenda'),
    path('add/', add_agenda_view, name='add_agenda'),
    path('edit/<int:agenda_id>/', edit_agenda_view, name='edit_agenda'),
    path('delete/<int:agenda_id>/', delete_agenda_view, name='delete_agenda'),
]