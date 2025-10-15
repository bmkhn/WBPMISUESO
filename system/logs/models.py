from django.db import models
from django.conf import settings

class LogEntry(models.Model):
	ACTION_CHOICES = [
		('CREATE', 'Created'),
		('UPDATE', 'Updated'),
		('DELETE', 'Deleted'),
	]
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="logs_entries")
	action = models.CharField(max_length=16, choices=ACTION_CHOICES)
	model = models.CharField(max_length=64)
	object_id = models.PositiveIntegerField()
	object_repr = models.CharField(max_length=200)
	timestamp = models.DateTimeField(auto_now_add=True)
	details = models.TextField(blank=True)
	url = models.CharField(max_length=300, blank=True)
	is_notification = models.BooleanField(default=False)
	notification_date = models.DateTimeField(null=True, blank=True)

	def __str__(self):
		return f"{self.get_action_display()} {self.model} ({self.object_repr}) by {self.user}" 
