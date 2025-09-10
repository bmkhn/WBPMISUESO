from django.urls import path
from .views import experts_view, expert_profile_view

urlpatterns = [
    path('', experts_view, name='experts'),
    path('profile/', expert_profile_view, name='expert_profile'), # Add Expert ID Later
]