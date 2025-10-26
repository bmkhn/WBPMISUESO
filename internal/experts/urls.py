from django.urls import path
from .views import experts_view, expert_profile_view, generate_team_view

urlpatterns = [
    path('', experts_view, name='experts'),
    # FIX: Made the URL dynamic to accept the expert's ID
    path('profile/<int:user_id>/', expert_profile_view, name='expert_profile'),
    path('generate-team/', generate_team_view, name='generate_team'),
]