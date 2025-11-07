from django.urls import path
from .views import add_submission_requirement, submission_admin_view, edit_submission, delete_submission

urlpatterns = [
    path('', submission_admin_view, name='submissions_admin'),
    path('add/', add_submission_requirement, name='add_submission'),
    path('add/<int:project_id>/', add_submission_requirement, name='add_submission'),
    path('<int:pk>/edit/', edit_submission, name='edit_submission'),
    path('<int:pk>/delete/', delete_submission, name='delete_submission'),
]