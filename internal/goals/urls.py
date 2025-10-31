from django.urls import path
from .views import (
    goal_view,
    api_goals, api_goal_detail, api_goal_qualifiers, api_goal_filters,
    add_goal_view, edit_goal_view,
)

urlpatterns = [
    path('', goal_view, name='goal'),
    # JSON API used by goals.html frontend
    path('api/goals/', api_goals, name='api_goals'),
    path('api/goals/<int:goal_id>/', api_goal_detail, name='api_goal_detail'),
    path('api/goals/<int:goal_id>/qualifiers/', api_goal_qualifiers, name='api_goal_qualifiers'),
    path('api/filters/', api_goal_filters, name='api_goal_filters'),
    # Server-rendered add/edit pages
    path('add/', add_goal_view, name='add_goal'),
    path('edit/<int:goal_id>/', edit_goal_view, name='edit_goal'),
]