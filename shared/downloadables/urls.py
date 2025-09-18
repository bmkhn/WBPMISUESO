from django.urls import path
from .views import (
	downloadable_dispatcher,
	add_downloadable,
	downloadable_download,
	downloadable_delete,
	downloadable_archive,
	downloadable_unarchive,
	downloadable_make_public,
	downloadable_make_private,
)

urlpatterns = [
	path('', downloadable_dispatcher, name='downloadable_dispatcher'),
	path('add/', add_downloadable, name='add_downloadable'),
	path('download/<int:pk>/', downloadable_download, name='downloadable_download'),
	path('delete/<int:pk>/', downloadable_delete, name='downloadable_delete'),
	path('archive/<int:pk>/', downloadable_archive, name='downloadable_archive'),
	path('unarchive/<int:pk>/', downloadable_unarchive, name='downloadable_unarchive'),
	path('make_public/<int:pk>/', downloadable_make_public, name='downloadable_make_public'),
	path('make_private/<int:pk>/', downloadable_make_private, name='downloadable_make_private'),
]
