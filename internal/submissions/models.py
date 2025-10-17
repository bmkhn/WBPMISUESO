
from django.db import models
from django.conf import settings
from shared.projects.models import Project, ProjectEvent
from shared.downloadables.models import Downloadable

class Submission(models.Model):
	project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='submissions')
	downloadable = models.ForeignKey(Downloadable, on_delete=models.CASCADE, related_name='submissions')
	deadline = models.DateTimeField()
	notes = models.TextField(blank=True, null=True)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_submissions')
	created_at = models.DateTimeField(auto_now_add=True)

	# Submission/response fields
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

	def get_status_display(self):
		return dict(self.SUBMISSION_STATUS_CHOICES).get(self.status, self.status)