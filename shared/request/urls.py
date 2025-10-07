from django.urls import path
from .views import request_dispatcher

urlpatterns = [
    path('', request_dispatcher, name='request_dispatcher'),
]