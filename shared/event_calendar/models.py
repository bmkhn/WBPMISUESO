from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from system.utils.file_validators import validate_file_size


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
	notes_attachment = models.FileField(upload_to='meeting_attachments/', blank=True, null=True, help_text='Optional file attachment for meeting notes', validators=[validate_file_size])
	participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='meeting_participants')
	STATUS_CHOICES = [
		("SCHEDULED", "Scheduled"),
		("ONGOING", "Ongoing"),
		("COMPLETED", "Completed"),
		("CANCELLED", "Cancelled"),
	]
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="SCHEDULED")

	class Meta:
		indexes = [
			# CRITICAL: Scheduler query (runs daily at midnight)
			# Query: MeetingEvent.objects.filter(status='SCHEDULED', datetime__date=today)
			models.Index(fields=['status', 'datetime'], name='meeting_sched_date_idx'),
			# Calendar view: Participant filtering
			models.Index(fields=['datetime'], name='meeting_datetime_idx'),
			# Creation tracking
			models.Index(fields=['-created_at'], name='meeting_created_idx'),
			# Creator lookup
			models.Index(fields=['created_by', '-created_at'], name='meeting_creator_idx'),
			# Status-based filtering (SCHEDULED, ONGOING, COMPLETED)
			models.Index(fields=['status', '-datetime'], name='meeting_status_idx'),
		]
		verbose_name = 'Meeting Event'
		verbose_name_plural = 'Meeting Events'
		ordering = ['datetime']

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
	from system.utils.email_utils import async_send_meeting_event_added
	
	if hasattr(instance, '_skip_log'):
		return
	action = 'CREATE' if created else 'UPDATE'
	
	event_date = instance.datetime.strftime('%Y-%m-%d')
	url = f"{reverse('calendar')}?date={event_date}"
	
	if created:
		details = f"New meeting scheduled for {instance.datetime.strftime('%B %d, %Y at %I:%M %p')}"
		
		# Send email to all participants when meeting is created
		participants = instance.participants.all()
		participant_emails = [p.email for p in participants if p.email]
		
		if participant_emails:
			async_send_meeting_event_added(
				recipient_emails=participant_emails,
				meeting_event=instance
			)
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


@receiver(m2m_changed, sender=MeetingEvent.participants.through)
def send_email_on_participant_added(sender, instance, action, pk_set, **kwargs):
	"""Send email when new participants are added to a meeting"""
	from system.utils.email_utils import async_send_meeting_event_added
	
	if action == "post_add" and pk_set:
		# Get the newly added participants
		from django.contrib.auth import get_user_model
		User = get_user_model()
		new_participants = User.objects.filter(pk__in=pk_set)
		participant_emails = [p.email for p in new_participants if p.email]
		
		if participant_emails:
			async_send_meeting_event_added(
				recipient_emails=participant_emails,
				meeting_event=instance
			)