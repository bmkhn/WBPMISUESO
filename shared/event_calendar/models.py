from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


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

	def save(self, *args, **kwargs):
		# Only set updated_at if this is an update (object already exists)
		if self.pk:
			from django.utils import timezone
			self.updated_at = timezone.now()
		super().save(*args, **kwargs)

	def get_status_display(self):
		return dict(self.STATUS_CHOICES).get(self.status, self.status)

	def __str__(self):
		return f"{self.title} (Meeting)"


@receiver(post_save, sender=MeetingEvent)
def log_meeting_event_action(sender, instance, created, **kwargs):
	from system.logs.models import LogEntry
	# Skip logging if this is being called from within a signal to avoid duplicates
	if hasattr(instance, '_skip_log'):
		return
	action = 'CREATE' if created else 'UPDATE'
	LogEntry.objects.create(
		user=instance.created_by if created else instance.updated_by,
		action=action,
		model='MeetingEvent',
		object_id=instance.id,
		object_repr=str(instance),
		details=f"Status: {instance.get_status_display()}"
	)


@receiver(post_delete, sender=MeetingEvent)
def log_meeting_event_delete(sender, instance, **kwargs):
	from system.logs.models import LogEntry
	LogEntry.objects.create(
		user=instance.updated_by,
		action='DELETE',
		model='MeetingEvent',
		object_id=instance.id,
		object_repr=str(instance),
		details=f"Status: {instance.get_status_display()}"
	)