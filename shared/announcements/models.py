from django.db import models
from system.users.models import User

class Announcement(models.Model):
	title = models.CharField(max_length=255, blank=False)
	body = models.TextField(blank=False)
	scheduled_at = models.DateTimeField(null=True, blank=True)
	cover_photo = models.ImageField(upload_to='announcements/', null=True, blank=True)
	published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='published_announcements', blank=False)
	published_at = models.DateTimeField(auto_now_add=True, blank=False)
	edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_announcements')
	edited_at = models.DateTimeField(null=True, blank=True)

	def __str__(self):
		return self.title