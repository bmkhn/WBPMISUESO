from django.urls import path
from .views import inbox_view

urlpatterns = [
    path('', inbox_view, name='inbox'),
]