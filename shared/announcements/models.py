from django.db import models
from system.users.models import User

class Announcement(models.Model):
	title = models.CharField(max_length=255, blank=False)
	body = models.TextField(blank=False)
	is_scheduled = models.BooleanField(default=False)
	scheduled_at = models.DateTimeField(null=True, blank=True)
	scheduled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='scheduled_announcements')
	cover_photo = models.ImageField(upload_to='announcements/', null=True, blank=True)
	published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='published_announcements')
	published_at = models.DateTimeField(null=True, blank=True)
	edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_announcements')
	edited_at = models.DateTimeField(null=True, blank=True)
	archived = models.BooleanField(default=False)

	def __str__(self):
		return self.title