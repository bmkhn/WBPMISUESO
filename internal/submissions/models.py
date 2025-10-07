from django.db import models
from django.conf import settings
from shared.projects.models import Project, ProjectEvent
from shared.downloadables.models import Downloadable

# Submission Requirement (by UESO, VP, Director)
class SubmissionRequirement(models.Model):
	projects = models.ManyToManyField(Project, related_name='submission_requirements')
	downloadables = models.ManyToManyField(Downloadable, related_name='submission_requirements')
	deadline = models.DateTimeField()
	notes = models.TextField(blank=True, null=True)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_submission_requirements')
	created_at = models.DateTimeField(auto_now_add=True)
	SUBMISSION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
		('REVIEWED', 'Reviewed'),
        ('COMPLETED', 'Completed'),
        ('OVERDUE', 'Overdue'),
    ]
	status = models.CharField(max_length=32, choices=SUBMISSION_STATUS_CHOICES, default='PENDING')
	reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_submission_requirements')
	reviewed_at = models.DateTimeField(null=True, blank=True)

# Submission Response (by Faculty)
class SubmissionResponse(models.Model):
	requirement = models.ForeignKey(SubmissionRequirement, on_delete=models.CASCADE, related_name='responses')
	files = models.ManyToManyField(Downloadable, related_name='submission_responses')
	submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='submitted_submission_responses')
	submitted_at = models.DateTimeField(auto_now_add=True)

	# Submission Type [Final] 
	for_product_production = models.BooleanField(default=False)
	for_research = models.BooleanField(default=False)
	for_extension = models.BooleanField(default=False)

	# Submission Type [Event]
	event = models.ForeignKey(ProjectEvent, on_delete=models.SET_NULL, null=True, blank=True, related_name='submission_responses')
	num_trained_individuals = models.PositiveIntegerField(null=True, blank=True)
	image_event = models.ImageField(upload_to='submissions/event_images/', null=True, blank=True)
	image_description = models.TextField(blank=True, null=True)