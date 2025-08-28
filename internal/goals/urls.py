from django.urls import path
from .views import goal_view

urlpatterns = [
    path('', goal_view, name='goal'),
]