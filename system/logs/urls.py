from django.urls import path
from .views import logs_view

urlpatterns = [
    path('', logs_view, name='logs'),
]