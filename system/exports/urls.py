from django.urls import path
from .views import exports_view, export_manage_user, export_project, export_log, export_budget, export_goals

urlpatterns = [
    path('', exports_view, name='exports'),
    path('manage_user/', export_manage_user, name='export_manage_user'),
    path('projects/', export_project, name='export_project'),
    path('logs/', export_log, name='export_log'),
    path('budgets/', export_budget, name='export_budget'),
    path('goals/', export_goals, name='export_goals'),
]