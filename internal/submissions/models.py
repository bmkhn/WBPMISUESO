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
		('PENDING', 'Pending'),                 				# Awaiting faculty submission
		('SUBMITTED', 'Submitted to College Coordinator'),      # Faculty submitted, awaiting coordinator review
		('REVISION_REQUESTED', 'Revision Requested'),   		# Coordinator requested revision
		('FORWARDED', 'Forwarded to UESO'),     				# Coordinator forwarded to UESO/Director/VP
		('APPROVED', 'Approved'),               				# UESO/Director/VP approved
		('REJECTED', 'Rejected'),               				# UESO/Director/VP rejected
		('OVERDUE', 'Overdue'),                 				# Missed deadline
	]

	status = models.CharField(max_length=32, choices=SUBMISSION_STATUS_CHOICES, default='PENDING')
	revision_count = models.PositiveIntegerField(default=0)
	rejection_count = models.PositiveIntegerField(default=0)
	is_late_submission = models.BooleanField(default=False)
	reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_submissions')
	reviewed_at = models.DateTimeField(null=True, blank=True)
	reason_for_revision = models.TextField(blank=True, null=True)
	authorized_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='final_approved_submissions')
	authorized_at = models.DateTimeField(null=True, blank=True)
	reason_for_rejection = models.TextField(blank=True, null=True)
	updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_submissions')
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		indexes = [
			# Most critical: Status filtering (heavily used in views)
			models.Index(fields=['status', '-deadline'], name='sub_status_deadline_idx'),
			# Deadline sorting and filtering (primary sort field)
			models.Index(fields=['-deadline'], name='sub_deadline_idx'),
			# Project lookup (foreign key relationship)
			models.Index(fields=['project', 'status'], name='sub_project_status_idx'),
			# Downloadable/form type filtering
			models.Index(fields=['downloadable', 'status'], name='sub_form_status_idx'),
			# Coordinator college filtering (joins through project leader)
			models.Index(fields=['project', '-created_at'], name='sub_project_created_idx'),
			# Submission workflow tracking
			models.Index(fields=['submitted_at', 'status'], name='sub_submitted_idx'),
			# Approval workflow for event submissions
			models.Index(fields=['status', 'event'], name='sub_status_event_idx'),
			# Late submission tracking
			models.Index(fields=['is_late_submission', 'status'], name='sub_late_status_idx'),
			# Admin review queue (FORWARDED status priority)
			models.Index(fields=['status', 'reviewed_at'], name='sub_review_queue_idx'),
		]
		verbose_name = 'Submission'
		verbose_name_plural = 'Submissions'

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

	@property
	def submitted_form_link(self):
		if self.file:
			return self.file.url
		elif self.image_event:
			return self.image_event.url
		return ""
	
	@property
	def downloadable_link(self):
		if self.downloadable and self.downloadable.file:
			return self.downloadable.file.url
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
    """
    Update project event_progress and has_final_submission fields.
    Also auto-complete projects when conditions are met.
    """
    project = instance.project
    
    # Handle APPROVED event submissions
    if instance.downloadable.submission_type == 'event' and instance.status == 'APPROVED':
        # Count all APPROVED event submissions for this project
        approved_count = Submission.objects.filter(
            project=project,
            downloadable__submission_type='event',
            status='APPROVED'
        ).count()
        project.event_progress = approved_count
        
        # Auto-complete project if all events are done
        if project.estimated_events > 0 and project.event_progress >= project.estimated_events:
            if project.status == 'IN_PROGRESS':
                project.status = 'COMPLETED'
                project.save(update_fields=['event_progress', 'status'])
            else:
                project.save(update_fields=['event_progress'])
        else:
            project.save(update_fields=['event_progress'])
    
    # Handle APPROVED final submissions
    elif instance.downloadable.submission_type == 'final' and instance.status == 'APPROVED':
        project.has_final_submission = True
        
        # Auto-complete project when final submission is approved
        if project.status == 'IN_PROGRESS':
            project.status = 'COMPLETED'
            project.save(update_fields=['has_final_submission', 'status'])
        else:
            project.save(update_fields=['has_final_submission'])


class SubmissionUpdate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    status = models.CharField(max_length=32)
    viewed = models.BooleanField(default=False)
    updated_at = models.DateTimeField()

    class Meta:
        unique_together = ('user', 'submission', 'status')
        indexes = [
            # User update feed (unread submissions)
            models.Index(fields=['user', 'viewed', '-updated_at'], name='subupd_user_view_idx'),
            # Submission-specific updates
            models.Index(fields=['submission', '-updated_at'], name='subupd_sub_date_idx'),
        ]
