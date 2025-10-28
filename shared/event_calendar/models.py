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
	from django.urls import reverse
	
	if hasattr(instance, '_skip_log'):
		return
	action = 'CREATE' if created else 'UPDATE'
	
	event_date = instance.datetime.strftime('%Y-%m-%d')
	url = f"{reverse('calendar')}?date={event_date}"
	
	if created:
		details = f"New meeting scheduled for {instance.datetime.strftime('%B %d, %Y at %I:%M %p')}"
	else:
		details = f"Meeting has been updated"
	
	log_user = instance.updated_by if instance.updated_by else instance.created_by
	
	LogEntry.objects.create(
		user=log_user,
		action=action,
		model='MeetingEvent',
		object_id=instance.id,
		object_repr=instance.title,
		details=details,
		url=url,
		is_notification=True
	)


@receiver(post_delete, sender=MeetingEvent)
def log_meeting_event_delete(sender, instance, **kwargs):
	from system.logs.models import LogEntry
	log_user = instance.updated_by if instance.updated_by else instance.created_by
	LogEntry.objects.create(
		user=log_user,
		action='DELETE',
		model='MeetingEvent',
		object_id=instance.id,
		object_repr=str(instance),
		details=f"Status: {instance.get_status_display()}",
		is_notification=True
	)