from django.urls import path
from .views import budget_dispatcher

urlpatterns = [
    path('', budget_dispatcher, name='budget_dashboard'),
]