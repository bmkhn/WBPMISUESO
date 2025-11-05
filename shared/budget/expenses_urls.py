from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.budget_view, name='dashboard'),
    path('project/<int:pk>/', views.faculty_project_budget_view, name='project'),
]


