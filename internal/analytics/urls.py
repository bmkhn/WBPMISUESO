from django.urls import path
from .views import analytics_view

urlpatterns = [
    path('', analytics_view, name='analytics')
]