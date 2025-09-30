from django.db import models
from django.conf import settings


class MeetingEvent(models.Model):
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	datetime = models.DateTimeField()
	location = models.CharField(max_length=255, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_meeting_events')
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_meeting_events')
	notes = models.TextField(blank=True, null=True)
	participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='meeting_participants')
	STATUS_CHOICES = [
		("SCHEDULED", "Scheduled"),
		("COMPLETED", "Completed"),
		("CANCELLED", "Cancelled"),
	]
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="SCHEDULED")

	def get_status_display(self):
		return dict(self.STATUS_CHOICES).get(self.status, self.status)

	def __str__(self):
		return f"{self.title} (Meeting)"