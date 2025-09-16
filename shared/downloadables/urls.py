from django.urls import path
from .views import downloadable_dispatcher

urlpatterns = [
	path('', downloadable_dispatcher, name='downloadable_dispatcher'),
]
