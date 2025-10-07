from django.urls import path
from .views import add_submission_requirement, submission_admin_view

urlpatterns = [
    path('', submission_admin_view, name='submissions_admin'),
    path('add/', add_submission_requirement, name='add_submission'),
]