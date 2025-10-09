from django.urls import path
from .views import exports_view, export_manage_user, export_project, export_log, export_budget, export_goals, export_download, reject_export_request, approve_export_request

urlpatterns = [
    path('', exports_view, name='exports'),
    path('manage_user/', export_manage_user, name='export_manage_user'),
    path('projects/', export_project, name='export_project'),
    path('logs/', export_log, name='export_log'),
    path('budgets/', export_budget, name='export_budget'),
    path('goals/', export_goals, name='export_goals'),
    path('download/<int:request_id>/', export_download, name='export_download'),
    path('reject/<int:request_id>/', reject_export_request, name='reject_export_request'),
    path('approve/<int:request_id>/', approve_export_request, name='approve_export_request'),
]