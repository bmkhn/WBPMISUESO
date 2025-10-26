from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from system.users.models import User

class Announcement(models.Model):
	def delete(self, *args, **kwargs):
		# Delete associated cover photo from storage
		if self.cover_photo and self.cover_photo.storage and self.cover_photo.storage.exists(self.cover_photo.name):
			self.cover_photo.storage.delete(self.cover_photo.name)
		super().delete(*args, **kwargs)
		
	title = models.CharField(max_length=255, blank=False)
	body = models.TextField(blank=False)
	is_scheduled = models.BooleanField(default=False)
	scheduled_at = models.DateTimeField(null=True, blank=True)
	scheduled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='scheduled_announcements')
	cover_photo = models.ImageField(upload_to='announcements/', null=True, blank=True, default=('announcements/announcements.png'))
	published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='published_announcements')
	published_at = models.DateTimeField(null=True, blank=True)
	edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_announcements')
	edited_at = models.DateTimeField(null=True, blank=True)
	archived = models.BooleanField(default=False)

	def __str__(self):
		return self.title
	
	def save(self, *args, **kwargs):
		# Only set updated_at if this is an update (object already exists)
		if self.pk:
			from django.utils import timezone
			self.updated_at = timezone.now()
		super().save(*args, **kwargs)


@receiver(post_save, sender=Announcement)
def log_announcement_action(sender, instance, created, **kwargs):
	from system.logs.models import LogEntry
	# Skip logging if this is being called from within a signal to avoid duplicates
	if hasattr(instance, '_skip_log'):
		return
	action = 'CREATE' if created else 'UPDATE'
	user = instance.published_by if created else instance.edited_by
	
	# Only create notification for published announcements
	is_notification = bool(instance.published_at)
	
	LogEntry.objects.create(
		user=user,
		action=action,
		model='Announcement',
		object_id=instance.id,
		object_repr=str(instance),
		details=f"Title: {instance.title}",
		is_notification=is_notification
	)


@receiver(post_delete, sender=Announcement)
def log_announcement_delete(sender, instance, **kwargs):
	from system.logs.models import LogEntry
	LogEntry.objects.create(
		user=instance.edited_by or instance.published_by,
		action='DELETE',
		model='Announcement',
		object_id=instance.id,
		object_repr=str(instance),
		details=f"Title: {instance.title}"
	)
	

