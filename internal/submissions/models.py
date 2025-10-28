from django.db import models
from django.conf import settings
from django.urls import reverse
from shared.projects.models import Project, ProjectEvent
from shared.downloadables.models import Downloadable
from system.logs.models import LogEntry
from django.dispatch import receiver
from django.db.models.signals import post_save
import os


class Submission(models.Model):
	project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='submissions')
	downloadable = models.ForeignKey(Downloadable, on_delete=models.CASCADE, related_name='submissions')
	deadline = models.DateTimeField()
	notes = models.TextField(blank=True, null=True)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_submissions')
	created_at = models.DateTimeField(auto_now_add=True)

	# Submission/Response fields
	submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='submitted_submissions')
	submitted_at = models.DateTimeField(null=True, blank=True)
	file = models.FileField(upload_to='submissions/files/', null=True, blank=True)

	# Submission Type [Final]
	for_product_production = models.BooleanField(default=False)
	for_research = models.BooleanField(default=False)
	for_extension = models.BooleanField(default=False)

	# Submission Type [Event]
	event = models.ForeignKey(ProjectEvent, on_delete=models.SET_NULL, null=True, blank=True, related_name='submissions')
	num_trained_individuals = models.PositiveIntegerField(null=True, blank=True)
	image_event = models.ImageField(upload_to='submissions/event_images/', null=True, blank=True)
	image_description = models.TextField(blank=True, null=True)


	# Status/Review
	SUBMISSION_STATUS_CHOICES = [
		('PENDING', 'Pending'),                 		# Awaiting faculty submission
		('SUBMITTED', 'Submitted'),             		# Faculty submitted, awaiting coordinator review
		('REVISION_REQUESTED', 'Revision Requested'),   # Coordinator requested revision
		('FORWARDED', 'Forwarded to UESO'),     		# Coordinator forwarded to UESO/Director/VP
		('APPROVED', 'Approved'),               		# UESO/Director/VP approved
		('REJECTED', 'Rejected'),               		# UESO/Director/VP rejected
		('OVERDUE', 'Overdue'),                 		# Missed deadline
	]

	status = models.CharField(max_length=32, choices=SUBMISSION_STATUS_CHOICES, default='PENDING')
	reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_submissions')
	reviewed_at = models.DateTimeField(null=True, blank=True)
	reason_for_revision = models.TextField(blank=True, null=True)
	authorized_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='final_approved_submissions')
	authorized_at = models.DateTimeField(null=True, blank=True)
	reason_for_rejection = models.TextField(blank=True, null=True)
	updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_submissions')
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.project.title + " - " + self.downloadable.name

	def get_status_display(self):
		return dict(self.SUBMISSION_STATUS_CHOICES).get(self.status, self.status)

	@property
	def submitted_form_name(self):
		if self.file:
			base = os.path.basename(self.file.name)
			return os.path.splitext(base)[0]
		elif self.image_event:
			base = os.path.basename(self.image_event.name)
			return os.path.splitext(base)[0]
		return ""

	@property
	def submitted_form_name_with_ext(self):
		if self.file:
			return os.path.basename(self.file.name)
		elif self.image_event:
			return os.path.basename(self.image_event.name)
		return ""

# Log creation and update actions for Submission
@receiver(post_save, sender=Submission)
def log_submission_action(sender, instance, created, **kwargs):
	user = instance.updated_by or instance.submitted_by or instance.created_by or None
	# project_submissions_details view expects (request, pk, submission_id) -> provide pk and submission_id for reverse
	url = reverse('project_submissions_details', args=[instance.project.pk, instance.id])
	
	# Create better detail messages
	if created:
		details = f"New submission for {instance.project.title} - {instance.downloadable.name}"
	else:
		status_messages = {
			'SUBMITTED': 'Submission has been submitted for review',
			'FORWARDED': 'Submission has been forwarded to administration',
			'REVISION_REQUESTED': 'Revision has been requested for this submission',
			'APPROVED': 'Submission has been approved',
			'REJECTED': 'Submission has been rejected',
		}
		details = status_messages.get(instance.status, f"Submission status: {instance.get_status_display()}")
	
	# Only log creation if created
	if created:
		LogEntry.objects.create(
			user=user,
			action='CREATE',
			model='Submission',
			object_id=instance.id,
			object_repr=f"{instance.project.title} - {instance.downloadable.name}",
			details=details,
			url=url,
			is_notification=True
		)
	# Only log update if not created and updated_at is set and not equal to submitted_at
	elif instance.updated_at and instance.updated_at != instance.submitted_at:
		LogEntry.objects.create(
			user=user,
			action='UPDATE',
			model='Submission',
			object_id=instance.id,
			object_repr=f"{instance.project.title} - {instance.downloadable.name}",
			details=details,
			url=url,
			is_notification=True
		)


@receiver(post_save, sender=Submission)
def update_project_event_progress(sender, instance, **kwargs):
    # Only trigger on APPROVED event submissions
    if instance.downloadable.submission_type == 'event' and instance.status == 'APPROVED':
        project = instance.project
        # Count all APPROVED event submissions for this project
        approved_count = Submission.objects.filter(
            project=project,
            downloadable__submission_type='event',
            status='APPROVED'
        ).count()
        project.event_progress = approved_count
        project.save(update_fields=['event_progress'])


class SubmissionUpdate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    status = models.CharField(max_length=32)
    viewed = models.BooleanField(default=False)
    updated_at = models.DateTimeField()

    class Meta:
        unique_together = ('user', 'submission', 'status')
