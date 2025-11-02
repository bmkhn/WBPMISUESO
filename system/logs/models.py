from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

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

	class Meta:
		indexes = [
			# Primary listing: Timestamp ordering
			models.Index(fields=['-timestamp'], name='log_timestamp_idx'),
			# User activity tracking
			models.Index(fields=['user', '-timestamp'], name='log_user_time_idx'),
			# Action filtering (CREATE, UPDATE, DELETE)
			models.Index(fields=['action', '-timestamp'], name='log_action_time_idx'),
			# Model filtering (Project, Submission, etc.)
			models.Index(fields=['model', '-timestamp'], name='log_model_time_idx'),
			# Combined filtering (common in admin views)
			models.Index(fields=['model', 'action', '-timestamp'], name='log_filter_idx'),
			# Notification creation (signal trigger)
			models.Index(fields=['is_notification', 'timestamp'], name='log_notif_idx'),
			# Object-specific logs
			models.Index(fields=['model', 'object_id'], name='log_object_idx'),
		]
		verbose_name = 'Log Entry'
		verbose_name_plural = 'Log Entries'
		ordering = ['-timestamp']

	def __str__(self):
		return f"{self.get_action_display()} {self.model} ({self.object_repr}) by {self.user}"


@receiver(post_save, sender=LogEntry)
def create_notifications_from_log_entry(sender, instance, created, **kwargs):
	"""
	Automatically create notifications when a log entry marked as is_notification is created
	"""
	if created and instance.is_notification:
		from system.notifications.utils import create_notifications_from_log
		create_notifications_from_log(instance)
