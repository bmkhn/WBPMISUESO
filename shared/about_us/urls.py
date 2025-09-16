from django.urls import path
from .views import about_us_dispatcher

urlpatterns = [
	path('', about_us_dispatcher, name='about_us_dispatcher'),
]
