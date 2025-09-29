from django.urls import path
from .views import about_us_dispatcher, edit_about_us

urlpatterns = [
	path('', about_us_dispatcher, name='about_us_dispatcher'),
	path('edit/', edit_about_us, name='edit_about_us'),
]