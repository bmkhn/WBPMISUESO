from django.urls import path
from .views import (
    budget_dispatcher, budget_edit_dashboard, edit_budget_allocation,
    edit_external_funding, create_budget_allocation, delete_budget_allocation,
    budget_history_view, budget_sponsor_view
)

urlpatterns = [
    path('', budget_dispatcher, name='budget_dashboard'),
    path('edit/', budget_edit_dashboard, name='budget_edit_dashboard'),
    path('edit/allocation/<int:allocation_id>/', edit_budget_allocation, name='edit_budget_allocation'),
    path('edit/funding/<int:funding_id>/', edit_external_funding, name='edit_external_funding'),
    path('create/allocation/', create_budget_allocation, name='create_budget_allocation'),
    path('delete/allocation/<int:allocation_id>/', delete_budget_allocation, name='delete_budget_allocation'),
    path('history/', budget_history_view, name='budget_history'),
    path('sponsors/', budget_sponsor_view, name='budget_sponsors'),
]