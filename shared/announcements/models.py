from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from system.users.models import User
from django.templatetags.static import static

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
	cover_photo = models.ImageField(upload_to='announcements/', null=True, blank=True)
	published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='published_announce')
	published_at = models.DateTimeField(null=True, blank=True)
	edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_announcements')
	edited_at = models.DateTimeField(null=True, blank=True)
	archived = models.BooleanField(default=False)

	class Meta:
		indexes = [
			# CRITICAL: Scheduler query optimization (runs every minute)
			# Query: Announcement.objects.filter(is_scheduled=True, scheduled_at__lte=now, published_at__isnull=True)
			models.Index(fields=['is_scheduled', 'scheduled_at', 'published_at'], name='ann_scheduler_idx'),
			# Most common: Published, non-archived announcements sorted by date
			# Query: Announcement.objects.filter(published_at__isnull=False, archived=False).order_by('-published_at')
			models.Index(fields=['published_at', 'archived'], name='ann_published_idx'),
			models.Index(fields=['archived', '-published_at'], name='ann_active_list_idx'),
			# Search optimization (title and body searches)
			models.Index(fields=['title'], name='ann_title_search_idx'),
			# Date range filtering
			models.Index(fields=['published_at'], name='ann_pub_date_idx'),
			# Publisher tracking
			models.Index(fields=['published_by', '-published_at'], name='ann_publisher_idx'),
			# Draft management (unpublished announcements)
			models.Index(fields=['published_at', '-scheduled_at'], name='ann_draft_idx'),
		]
		verbose_name = 'Announcement'
		verbose_name_plural = 'Announcements'
		ordering = ['-published_at']

	def __str__(self):
		return self.title
	
	@property
	def get_cover_photo_url(self):
		"""Return the cover photo URL or default image"""
		if self.cover_photo:
			try:
				return self.cover_photo.url
			except ValueError:
				pass
			except AttributeError:
				pass
		return static('announce.png')

	def save(self, *args, **kwargs):
		# Only set updated_at if this is an update (object already exists)
		if self.pk:
			from django.utils import timezone
			self.updated_at = timezone.now()
		super().save(*args, **kwargs)

@receiver(post_save, sender=Announcement)
def log_announcement_action(sender, instance, created, **kwargs):
	from system.logs.models import LogEntry
	from django.urls import reverse
	
	# Skip logging if this is being called from within a signal to avoid duplicates
	if hasattr(instance, '_skip_log'):
		return
	action = 'CREATE' if created else 'UPDATE'
	user = instance.published_by if created else instance.edited_by
	
	# Only create notification for published announcements
	is_notification = bool(instance.published_at)
	
	# URL to announcement details
	url = reverse('announcement_details', args=[instance.id])
	
	# Create better detail messages
	if created and is_notification:
		details = "A new announcement has been published"
	elif not created:
		details = "An announcement has been updated"
	else:
		details = "A new announcement draft has been created"
	
	LogEntry.objects.create(
		user=user,
		action=action,
		model='Announcement',
		object_id=instance.id,
		object_repr=instance.title,
		details=details,
		url=url,
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
	

