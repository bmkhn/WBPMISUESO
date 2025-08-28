from django.urls import path
from .views import experts_view

urlpatterns = [
    path('', experts_view, name='experts'),
]