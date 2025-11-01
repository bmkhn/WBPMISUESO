from django.conf import settings
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from system.users.models import College


class Agenda(models.Model):
	name = models.CharField(max_length=255)
	description = models.TextField()
	concerned_colleges = models.ManyToManyField(College, related_name='agendas')
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_agendas')
	updated_at = models.DateTimeField(null=True, blank=True)
	updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_agendas')

	class Meta:
		indexes = [
			# Primary lookup by ID (auto-indexed by Django as primary key)
			# Listing by creation date (most recent first)
			models.Index(fields=['-created_at'], name='agenda_created_idx'),
			# Filtering by creator for audit trails
			models.Index(fields=['created_by', '-created_at'], name='agenda_creator_idx'),
			# Name search optimization (for future search features)
			models.Index(fields=['name'], name='agenda_name_idx'),
		]
		verbose_name = 'Agenda'
		verbose_name_plural = 'Agendas'

	def save(self, *args, **kwargs):
		# Only set updated_at if this is an update (object already exists)
		if self.pk:
			from django.utils import timezone
			self.updated_at = timezone.now()
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name


@receiver(post_save, sender=Agenda)
def log_agenda_action(sender, instance, created, **kwargs):
	from system.logs.models import LogEntry
	# Skip logging if this is being called from within a signal to avoid duplicates
	if hasattr(instance, '_skip_log'):
		return
	action = 'CREATE' if created else 'UPDATE'
	LogEntry.objects.create(
		user=instance.created_by if created else instance.updated_by,
		action=action,
		model='Agenda',
		object_id=instance.id,
		object_repr=str(instance),
		details=f"Concerned Colleges: {', '.join([college.name for college in instance.concerned_colleges.all()])}"
	)


@receiver(post_delete, sender=Agenda)
def log_agenda_delete(sender, instance, **kwargs):
	from system.logs.models import LogEntry
	LogEntry.objects.create(
		user=instance.updated_by,
		action='DELETE',
		model='Agenda',
		object_id=instance.id,
		object_repr=str(instance),
		details=f"Concerned Colleges: {', '.join([college.name for college in instance.concerned_colleges.all()])}"
	)